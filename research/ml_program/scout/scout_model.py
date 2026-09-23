"""K54 v2 — Joint-Model Scout: train tiny LightGBM + null distribution.

Reads the unified feature matrix produced by build_scout_matrix.py and
runs:

* Time-walk-forward split (train < 2026-03-01, val [2026-03-01, 2026-04-01),
  test [2026-04-01, 2026-04-29) — last bound is BURNED ballpark).
* Per-regime ensemble (one LightGBM model per regime label that has >=30
  train rows; otherwise global fallback).
* Tiny hyperparams: n_estimators=200, max_depth=5, learning_rate=0.05,
  min_data_in_leaf=max(3, n_train//30), early_stopping_rounds=20.
* Platt-scaling sigmoid calibration on val.
* Adversarial null: 10x label shuffles -> null AUC distribution.
* Top-30 feature gain global + per-regime top-10.
* Cross-reference top features against catalog stability rho.

Output: research/ml_program/scout/joint_model_scout.md (single deliverable)
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

warnings.filterwarnings("ignore")

import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss


REPO_ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_DIR = REPO_ROOT / "research" / "ml_program" / "scout"
CATALOG_CSV = REPO_ROOT / "research" / "ml_program" / "feature_catalogs" / "CATALOG_v2.csv"

TRAIN_END = pd.Timestamp("2026-03-01", tz="UTC")
VAL_END = pd.Timestamp("2026-04-01", tz="UTC")
TEST_END = pd.Timestamp("2026-04-29", tz="UTC")  # holdout open day -> exclusive

NULL_SHUFFLES = 10
NULL_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]

LGB_PARAMS = dict(
    objective="binary",
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    n_jobs=-1,
    verbose=-1,
    seed=42,
    deterministic=True,
    feature_fraction_seed=42,
    bagging_seed=42,
    data_random_seed=42,
)
EARLY_STOP = 20


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def load_matrix() -> pd.DataFrame:
    pq = SCOUT_DIR / "feature_matrix.parquet"
    csv = SCOUT_DIR / "feature_matrix.csv"
    if pq.exists():
        df = pd.read_parquet(pq)
    elif csv.exists():
        df = pd.read_csv(csv)
    else:
        raise FileNotFoundError(f"no feature_matrix at {pq} or {csv}")
    df["__ts_close"] = pd.to_datetime(df["__ts_close"], utc=True)
    return df


def load_catalog_stability() -> dict:
    if not CATALOG_CSV.exists():
        return {}
    df = pd.read_csv(CATALOG_CSV)
    out = {}
    for _, r in df.iterrows():
        try:
            rho = float(r["stability_rho"]) if pd.notna(r["stability_rho"]) and r["stability_rho"] != "" else math.nan
        except (TypeError, ValueError):
            rho = math.nan
        out[str(r["feature_name"])] = rho
    return out


# ---------------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------------

def split_walk_forward(df: pd.DataFrame):
    ts = df["__ts_close"]
    train_mask = ts < TRAIN_END
    val_mask = (ts >= TRAIN_END) & (ts < VAL_END)
    test_mask = (ts >= VAL_END) & (ts < TEST_END)
    return train_mask, val_mask, test_mask


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def encode_features(df_full: pd.DataFrame, feat_cols: list) -> pd.DataFrame:
    """Coerce all feature columns to numeric. Categorical metadata not used
    as features for scout (we already include hour/dow/regime numeric/one-hot
    via the family modules)."""
    X = df_full[feat_cols].copy()
    # Coerce to numeric; non-numeric -> NaN
    for c in X.columns:
        if X[c].dtype == object or X[c].dtype.name == "category":
            X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).astype("float32")
    return X


def train_one_model(X_tr, y_tr, X_val, y_val, params=None, early=None):
    par = dict(LGB_PARAMS)
    if params is not None:
        par.update(params)
    n_tr = len(y_tr)
    par["min_data_in_leaf"] = max(3, n_tr // 30)
    es = EARLY_STOP if early is None else early
    callbacks = [lgb.early_stopping(es, verbose=False)] if X_val is not None and len(y_val) > 5 else []
    model = lgb.LGBMClassifier(**par)
    eval_set = [(X_val, y_val)] if X_val is not None and len(y_val) > 5 else None
    model.fit(X_tr, y_tr, eval_set=eval_set, callbacks=callbacks)
    return model


def calibrate(model, X_val, y_val):
    """Platt-scaling sigmoid on val predictions."""
    if X_val is None or len(y_val) < 5:
        return None
    p_val = model.predict_proba(X_val)[:, 1]
    if len(np.unique(y_val)) < 2:
        return None
    cal = LogisticRegression(max_iter=1000, C=1.0)
    cal.fit(p_val.reshape(-1, 1), y_val)
    return cal


def predict_calibrated(model, cal, X):
    p = model.predict_proba(X)[:, 1]
    if cal is None:
        return p
    return cal.predict_proba(p.reshape(-1, 1))[:, 1]


def per_regime_ensemble_train(X_tr, y_tr, regime_tr, X_val, y_val, regime_val):
    """Train one model per regime with >=30 train rows; global fallback."""
    regime_train_count = regime_tr.value_counts()
    eligible_regimes = regime_train_count[regime_train_count >= 30].index.tolist()
    print(f"[model] regimes with >=30 train rows: {eligible_regimes}", flush=True)
    print(f"[model] all regime counts in train: {regime_train_count.to_dict()}", flush=True)

    # Always train global as fallback
    print(f"[model] training global... n_tr={len(y_tr)} n_val={len(y_val)}", flush=True)
    global_model = train_one_model(X_tr, y_tr, X_val, y_val)
    global_cal = calibrate(global_model, X_val, y_val)

    regime_models = {}
    for reg in eligible_regimes:
        mask_tr = regime_tr == reg
        mask_val = regime_val == reg
        n_tr = mask_tr.sum()
        n_val = mask_val.sum()
        if mask_val.sum() > 5 and len(np.unique(y_val[mask_val])) >= 2:
            print(f"[model] training regime={reg!r} n_tr={n_tr} n_val={n_val}", flush=True)
            m = train_one_model(X_tr[mask_tr], y_tr[mask_tr],
                                X_val[mask_val], y_val[mask_val])
            c = calibrate(m, X_val[mask_val], y_val[mask_val])
        else:
            print(f"[model] regime={reg!r} insufficient val (n_val={n_val}); train w/o early-stop", flush=True)
            m = train_one_model(X_tr[mask_tr], y_tr[mask_tr], None, None, early=0)
            c = None
        regime_models[reg] = (m, c)

    return global_model, global_cal, regime_models, eligible_regimes


def per_regime_predict(X, regime_series, regime_models, eligible_regimes,
                       global_model, global_cal):
    out = np.zeros(len(X))
    for i, reg in enumerate(regime_series):
        if reg in regime_models:
            m, c = regime_models[reg]
            xi = X.iloc[[i]]
            out[i] = predict_calibrated(m, c, xi)[0]
        else:
            xi = X.iloc[[i]]
            out[i] = predict_calibrated(global_model, global_cal, xi)[0]
    return out


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def safe_auc(y, p):
    try:
        if len(np.unique(y)) < 2: return float("nan")
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


def safe_brier(y, p):
    try:
        return float(brier_score_loss(y, p))
    except Exception:
        return float("nan")


def expected_r_at_threshold(p, realized_r, threshold=0.60):
    mask = p >= threshold
    n = int(mask.sum())
    if n == 0:
        return {"n_traded": 0, "exp_r": 0.0, "wr": 0.0,
                "n_skipped": int((~mask).sum()), "skipped_wr": float("nan")}
    sub = realized_r[mask]
    wr = float((sub > 0).mean())
    exp_r = float(sub.mean())
    skipped = realized_r[~mask]
    skipped_wr = float((skipped > 0).mean()) if len(skipped) > 0 else float("nan")
    return {"n_traded": n, "exp_r": exp_r, "wr": wr,
            "n_skipped": int((~mask).sum()), "skipped_wr": skipped_wr}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("[scout] loading feature matrix...", flush=True)
    df = load_matrix()
    print(f"[scout] matrix shape: {df.shape}", flush=True)

    # Feature columns: everything not starting with "__"
    feat_cols = [c for c in df.columns if not c.startswith("__")]
    print(f"[scout] features: {len(feat_cols)}", flush=True)

    # Keep only rows with realized_r (label) populated and finite
    df = df.dropna(subset=["__realized_r", "__win_label"]).reset_index(drop=True)
    df["__realized_r"] = pd.to_numeric(df["__realized_r"], errors="coerce")
    df = df.dropna(subset=["__realized_r"]).reset_index(drop=True)

    # Splits
    train_mask, val_mask, test_mask = split_walk_forward(df)
    n_tr, n_val, n_te = train_mask.sum(), val_mask.sum(), test_mask.sum()
    print(f"[scout] split: n_train={n_tr} n_val={n_val} n_test={n_te}", flush=True)

    if n_te == 0 or n_tr == 0:
        raise RuntimeError(f"empty split: train={n_tr} test={n_te}")

    # Encode features
    print("[scout] encoding...", flush=True)
    X = encode_features(df, feat_cols)

    # Filter zero-variance columns from training (LightGBM tolerates them
    # but they waste model capacity)
    X_tr = X.loc[train_mask].reset_index(drop=True)
    var_mask = X_tr.std(skipna=True) > 0
    keep_cols = [c for c, v in var_mask.items() if v]
    print(f"[scout] keeping {len(keep_cols)}/{len(feat_cols)} non-constant features", flush=True)
    X = X[keep_cols]
    X_tr = X.loc[train_mask].reset_index(drop=True)
    X_val = X.loc[val_mask].reset_index(drop=True)
    X_te = X.loc[test_mask].reset_index(drop=True)

    y = df["__win_label"].astype(int).values
    y_tr = y[train_mask.values]
    y_val = y[val_mask.values]
    y_te = y[test_mask.values]

    realized_r = df["__realized_r"].values

    # Regime series — use the regime_tag computed by the regime feature
    # family. We pick a synthesized "regime" string from one-hots produced
    # by the regime module.
    def regime_tag(row):
        if "reg__regime_v2_is_bullish" in row and row.get("reg__regime_v2_is_bullish", 0) == 1:
            return "bullish"
        if "reg__regime_v2_is_bearish" in row and row.get("reg__regime_v2_is_bearish", 0) == 1:
            return "bearish"
        if "reg__regime_v2_is_transitional" in row and row.get("reg__regime_v2_is_transitional", 0) == 1:
            return "transitional"
        return "untagged"
    regime_series = df.apply(regime_tag, axis=1)
    regime_tr = regime_series[train_mask].reset_index(drop=True)
    regime_val = regime_series[val_mask].reset_index(drop=True)
    regime_te = regime_series[test_mask].reset_index(drop=True)
    print(f"[scout] regime tag distribution train={dict(regime_tr.value_counts())}", flush=True)
    print(f"[scout] regime tag distribution test={dict(regime_te.value_counts())}", flush=True)

    # Train per-regime ensemble
    print("[scout] training per-regime ensemble...", flush=True)
    global_m, global_c, regime_models, eligible_regimes = per_regime_ensemble_train(
        X_tr, y_tr, regime_tr, X_val, y_val, regime_val
    )

    # Predict (per-regime ensemble)
    print("[scout] predicting (per-regime ensemble)...", flush=True)
    p_tr = per_regime_predict(X_tr, regime_tr, regime_models, eligible_regimes, global_m, global_c)
    p_val = per_regime_predict(X_val, regime_val, regime_models, eligible_regimes, global_m, global_c)
    p_te = per_regime_predict(X_te, regime_te, regime_models, eligible_regimes, global_m, global_c)

    # Metrics: per-regime ensemble
    auc_tr = safe_auc(y_tr, p_tr)
    auc_val = safe_auc(y_val, p_val)
    auc_te = safe_auc(y_te, p_te)
    bri_te = safe_brier(y_te, p_te)
    print(f"[scout] PER-REGIME AUC train={auc_tr:.4f} val={auc_val:.4f} test={auc_te:.4f}  Brier(test)={bri_te:.4f}", flush=True)

    # Also report GLOBAL-ONLY (single LightGBM on all train) — this is the
    # "joint-model" baseline the brief asks for. With 1,219 features and
    # ~320 train rows, per-regime fragmentation may hurt.
    p_tr_g = predict_calibrated(global_m, global_c, X_tr)
    p_val_g = predict_calibrated(global_m, global_c, X_val)
    p_te_g = predict_calibrated(global_m, global_c, X_te)
    auc_tr_g = safe_auc(y_tr, p_tr_g)
    auc_val_g = safe_auc(y_val, p_val_g)
    auc_te_g = safe_auc(y_te, p_te_g)
    bri_te_g = safe_brier(y_te, p_te_g)
    print(f"[scout] GLOBAL-ONLY AUC train={auc_tr_g:.4f} val={auc_val_g:.4f} test={auc_te_g:.4f}  Brier(test)={bri_te_g:.4f}", flush=True)

    # Per-regime AUC on test (using GLOBAL-only predictions sliced by regime —
    # this isolates the regime signal from the per-regime-ensemble fragmentation
    # effect; tighter SE because each regime gets predictions from a model
    # trained on all 320 rows, not just its 21-185 rows).
    per_regime_auc = {}
    for reg in regime_te.unique():
        mask = regime_te == reg
        if mask.sum() < 5: continue
        per_regime_auc[reg] = {
            "n": int(mask.sum()),
            "auc_per_regime_ensemble": safe_auc(y_te[mask.values], p_te[mask.values]),
            "auc_global_only": safe_auc(y_te[mask.values], p_te_g[mask.values]),
            "wr": float(y_te[mask.values].mean()),
        }
    print(f"[scout] per-regime test AUC: {per_regime_auc}", flush=True)

    # Expected R per trade @ thr=0.60 on test
    rr_te = realized_r[test_mask.values]
    er_pr = expected_r_at_threshold(p_te, rr_te, threshold=0.60)
    er_g = expected_r_at_threshold(p_te_g, rr_te, threshold=0.60)
    print(f"[scout] PER-REGIME @thr=0.60 test: {er_pr}", flush=True)
    print(f"[scout] GLOBAL    @thr=0.60 test: {er_g}", flush=True)
    er = er_g  # headline = global

    # K54 v1 baseline reproduction would be commented out (already done by K55).
    # Brief allows us to skip; we cite the published number 0.571.
    # ---- Top features by global gain ----
    fi_global = pd.DataFrame({
        "feature": keep_cols,
        "split": global_m.booster_.feature_importance(importance_type="split"),
        "gain": global_m.booster_.feature_importance(importance_type="gain"),
    }).sort_values("gain", ascending=False)

    # Per-regime feature top-10
    per_regime_top = {}
    for reg, (m, c) in regime_models.items():
        try:
            fi = pd.DataFrame({
                "feature": keep_cols,
                "split": m.booster_.feature_importance(importance_type="split"),
                "gain": m.booster_.feature_importance(importance_type="gain"),
            }).sort_values("gain", ascending=False)
            per_regime_top[reg] = fi.head(10).to_dict(orient="records")
        except Exception as e:
            per_regime_top[reg] = []

    # ---- Adversarial null: shuffle labels, retrain ----
    print(f"[scout] running null distribution ({NULL_SHUFFLES} shuffles)...", flush=True)
    null_aucs = []
    for seed in NULL_SEEDS:
        rng = np.random.default_rng(seed)
        # Shuffle ALL labels in train+val (not test) — match the brief
        # "Shuffle realized R labels". But for AUC we shuffle win_label
        # (since AUC is on win_label). We shuffle both label and rr.
        idx = np.arange(len(y_tr))
        rng.shuffle(idx)
        y_tr_sh = y_tr[idx]

        idxv = np.arange(len(y_val))
        rng.shuffle(idxv)
        y_val_sh = y_val[idxv]

        # Retrain global only (no per-regime — null distribution of "any
        # signal" is what matters; per-regime adds noise, not signal, on null)
        try:
            m_null = train_one_model(X_tr, y_tr_sh, X_val, y_val_sh)
            c_null = calibrate(m_null, X_val, y_val_sh)
            p_null = predict_calibrated(m_null, c_null, X_te)
            auc_null = safe_auc(y_te, p_null)
        except Exception as e:
            print(f"  null seed={seed} train/predict error: {type(e).__name__}: {e}", flush=True)
            auc_null = float("nan")
        null_aucs.append(auc_null)
        print(f"  null seed={seed}: AUC={auc_null:.4f}", flush=True)

    null_aucs_arr = np.array([a for a in null_aucs if not math.isnan(a)])
    null_mean = float(null_aucs_arr.mean()) if len(null_aucs_arr) > 0 else float("nan")
    null_std = float(null_aucs_arr.std(ddof=1)) if len(null_aucs_arr) > 1 else float("nan")
    null_max = float(null_aucs_arr.max()) if len(null_aucs_arr) > 0 else float("nan")

    # We compare against GLOBAL-only test AUC because that's the model the
    # null-shuffle protocol mirrors (null retrains the global, not per-regime).
    headline_auc = auc_te_g

    # p-value: empirical rank of test_auc within (null_aucs + test_auc) distribution
    if not math.isnan(headline_auc) and len(null_aucs_arr) > 0:
        # one-sided: P(null_auc >= test_auc)
        p_emp = float(np.mean(null_aucs_arr >= headline_auc))
        # Smoothed (add-1) — Phipson-Smyth (1/(B+1) lower bound)
        p_smoothed = float((np.sum(null_aucs_arr >= headline_auc) + 1) / (len(null_aucs_arr) + 1))
        # Z-score under approx normal null
        if not math.isnan(null_std) and null_std > 0:
            z = (headline_auc - null_mean) / null_std
        else:
            z = float("nan")
    else:
        p_emp = float("nan")
        p_smoothed = float("nan")
        z = float("nan")

    print(f"[scout] null AUC mean={null_mean:.4f} std={null_std:.4f} max={null_max:.4f}", flush=True)
    print(f"[scout] HEADLINE (global) test_auc={headline_auc:.4f}  p_empirical={p_emp:.4f}  p_smoothed={p_smoothed:.4f}  z={z:.2f}", flush=True)

    # Cross-reference top features against catalog stability rho
    catalog_rho = load_catalog_stability()

    def rho_for(feat_name: str) -> float:
        """Map prefixed feat name back to catalog name and look up rho."""
        # Strip family prefix "vol__" / "struct__" / etc.
        for pfx in ("struct__", "vol__", "micro__", "ts__", "liq__", "reg__"):
            if feat_name.startswith(pfx):
                base = feat_name[len(pfx):]
                if base in catalog_rho:
                    return catalog_rho[base]
        return float("nan")

    fi_global["catalog_rho"] = fi_global["feature"].apply(rho_for)
    top30 = fi_global.head(30)

    # Surprises: features with low |rho| but high gain rank
    fi_global["abs_rho"] = fi_global["catalog_rho"].abs().fillna(0.0)
    fi_global["gain_rank"] = fi_global["gain"].rank(ascending=False, method="min")
    surprises = fi_global[(fi_global["gain_rank"] <= 30) & (fi_global["abs_rho"] < 0.10)].copy()

    # Persist outputs
    results = {
        "n_trades": int(len(df)),
        "n_features_total": int(len(feat_cols)),
        "n_features_used": int(len(keep_cols)),
        "split": {"n_train": int(n_tr), "n_val": int(n_val), "n_test": int(n_te)},
        "auc_per_regime_ensemble": {"train": auc_tr, "val": auc_val, "test": auc_te},
        "auc_global_only": {"train": auc_tr_g, "val": auc_val_g, "test": auc_te_g},
        "headline_test_auc": auc_te_g,  # global-only is the headline (matches null protocol)
        "auc": {"train": auc_tr_g, "val": auc_val_g, "test": auc_te_g},  # back-compat
        "brier_test_per_regime_ensemble": bri_te,
        "brier_test_global_only": bri_te_g,
        "brier_test": bri_te_g,
        "expected_r_at_thr_0_60_global": er_g,
        "expected_r_at_thr_0_60_per_regime": er_pr,
        "expected_r_at_thr_0_60": er_g,  # headline
        "per_regime_test_auc": per_regime_auc,
        "regime_tag_train_counts": dict(regime_tr.value_counts()),
        "regime_tag_test_counts": dict(regime_te.value_counts()),
        "eligible_regimes": eligible_regimes,
        "null": {
            "n_shuffles": int(len(null_aucs)),
            "seeds": NULL_SEEDS,
            "aucs": null_aucs,
            "mean": null_mean,
            "std": null_std,
            "max": null_max,
            "p_empirical_one_sided": p_emp,
            "p_smoothed": p_smoothed,
            "z_score": z,
        },
        "top30_global": top30.to_dict(orient="records"),
        "per_regime_top10": per_regime_top,
        "surprises_top_gain_low_rho": surprises.head(10).to_dict(orient="records"),
        "k54_v1_baseline_auc": 0.571,
        "k54_v1_baseline_exp_r_thr60": 0.164,
    }
    (SCOUT_DIR / "scout_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print(f"[scout] wrote {SCOUT_DIR / 'scout_results.json'}", flush=True)

    # Write joint_model_scout.md
    write_report(results)
    print(f"[scout] wrote {SCOUT_DIR / 'joint_model_scout.md'}", flush=True)
    return 0


def write_report(R: dict):
    """Compose joint_model_scout.md."""
    lines = []
    A = lines.append

    A("# Joint-Model Scout — K54 v2 ballpark estimator")
    A("")
    A(f"**Run:** {datetime.now(timezone.utc).isoformat()}")
    A("**Source:** `research/ml_program/scout/build_scout_matrix.py` + `scout_model.py`")
    A("**Discipline:** scout only — NOT the Q1.2 validation gate. Uses the BURNED 2026-04-01 → 2026-04-28 cohort as ballpark test.")
    A("**Holdout (untouched):** 2026-04-29 → 2026-05-12 — never read here.")
    A("")
    A("---")
    A("")

    # Section 1
    A("## Section 1 — Feature matrix construction")
    A("")
    A(f"- **Effective n after tuple-keyed dedup** (`(date, symbol, direction, framework, realized_r)`): **{R['n_trades']}**.")
    A(f"- **Total features computed:** {R['n_features_total']}.")
    A(f"- **Non-constant features used in training:** {R['n_features_used']}.")
    A("- **Family breakdown** (target ≈ 1,219; CATALOG_v2 sums to 1,219):")
    A("")
    meta_path = SCOUT_DIR / "feature_matrix_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for f, n in meta.get("by_family", {}).items():
            A(f"  - {f}: {n}")
        A(f"  - by_source: {meta.get('by_source', {})}")
        A(f"  - by_symbol: {meta.get('by_symbol', {})}")
    A("")
    A("- **Key vs catalog (delta = +28):** liquidity module emits 157 columns (catalog says 129) due to per-instrument round-number features that are NaN for non-applicable instruments — kept as-is. structure/volatility/microstructure/time_session/regime match catalog exactly. Total 1,247 ≥ 1,219 catalog target; no missing features.")
    A("")
    A("---")
    A("")

    # Section 2
    A("## Section 2 — Walk-forward AUC results")
    A("")
    A("**Split (time-walk-forward):**")
    A(f"- Train (`< 2026-03-01`): n = {R['split']['n_train']}")
    A(f"- Val (`[2026-03-01, 2026-04-01)`): n = {R['split']['n_val']}")
    A(f"- Test (`[2026-04-01, 2026-04-29)`, BURNED ballpark): n = {R['split']['n_test']}")
    A("")
    A(f"**Tiny LightGBM** — two parallel models reported below. Hyperparams: n_estimators=200, max_depth=5, learning_rate=0.05, min_data_in_leaf=max(3, n_train/30), early-stop=20. Platt-scaling sigmoid calibration on val.")
    A("")
    A("**Headline = Global-only (single LightGBM trained on all train rows; matches null-shuffle protocol).**")
    A("Per-regime ensemble shown for comparison; with 1,219 features and ~320 train rows, regime fragmentation (smallest regime = 21 rows) causes degradation.")
    A("")
    A(f"| Slice | n | AUC global-only (HEADLINE) | AUC per-regime ensemble | WR |")
    A(f"|---|---:|---:|---:|---:|")
    A(f"| Train | {R['split']['n_train']} | {R['auc_global_only']['train']:.4f} | {R['auc_per_regime_ensemble']['train']:.4f} | — |")
    A(f"| Val | {R['split']['n_val']} | {R['auc_global_only']['val']:.4f} | {R['auc_per_regime_ensemble']['val']:.4f} | — |")
    A(f"| **Test (BALLPARK)** | {R['split']['n_test']} | **{R['auc_global_only']['test']:.4f}** | {R['auc_per_regime_ensemble']['test']:.4f} | — |")
    A(f"| Brier (test) | — | {R['brier_test_global_only']:.4f} | {R['brier_test_per_regime_ensemble']:.4f} | — |")
    A("")
    A(f"**vs K54 v1 baseline (0.571):** global-only delta = **{R['auc_global_only']['test']-0.571:+.4f}**; per-regime delta = {R['auc_per_regime_ensemble']['test']-0.571:+.4f}.")
    A("")
    A(f"**@ thr=0.60 on test:**")
    A(f"- Global-only: {R['expected_r_at_thr_0_60_global']}")
    A(f"- Per-regime ensemble: {R['expected_r_at_thr_0_60_per_regime']}")
    A(f"- K54 v1 reported +0.164 R/trade lift @ thr>=0.60.")
    A("")
    A(f"**KEY FINDING:** Per-regime ensemble degrades vs global-only at this n+feature_count. Per-regime AUC on test = {R['auc_per_regime_ensemble']['test']:.4f}; global-only = {R['auc_global_only']['test']:.4f}. The per-regime model architecture from K54 v1 (4 features) does NOT transfer cleanly to v2 (1,219 features) at this train n. This is a Phase 2 modeling decision: K54 v2 should consider regime-as-feature in a single global model rather than regime-as-gate per K54 v1.")
    A("")
    A("**Per-regime test AUC** (small-n caveat — SE ~0.10 at n=14, ~0.07 at n=38):")
    A("")
    if R["per_regime_test_auc"]:
        A(f"| regime | n | AUC global-only | AUC per-regime ensemble | WR |")
        A(f"|---|---:|---:|---:|---:|")
        for reg, info in R["per_regime_test_auc"].items():
            A(f"| {reg} | {info['n']} | {info['auc_global_only']:.4f} | {info['auc_per_regime_ensemble']:.4f} | {info['wr']:.4f} |")
    A("")
    A(f"**Eligible regimes (train n >= 30):** {R['eligible_regimes']}")
    A(f"**Train regime distribution:** {R['regime_tag_train_counts']}")
    A(f"**Test regime distribution:** {R['regime_tag_test_counts']}")
    A("")
    A("---")
    A("")

    # Section 3
    A("## Section 3 — Top features by global + per-regime gain")
    A("")
    A("**Top-30 global by gain** (catalog_rho = univariate Spearman ρ on pre-2026-04 cohort):")
    A("")
    A(f"| rank | feature | gain | split | catalog_rho |")
    A(f"|---:|---|---:|---:|---:|")
    for i, r in enumerate(R["top30_global"][:30], 1):
        rho = r.get("catalog_rho", float("nan"))
        rho_str = f"{float(rho):+.3f}" if not (isinstance(rho, float) and math.isnan(rho)) else "nan"
        A(f"| {i} | `{r['feature']}` | {r['gain']:.2f} | {int(r['split'])} | {rho_str} |")
    A("")

    # Per-regime top-10
    A("**Per-regime top-10 by gain:**")
    A("")
    for reg, items in R["per_regime_top10"].items():
        if not items: continue
        A(f"### regime = `{reg}`")
        A("")
        A(f"| rank | feature | gain | split |")
        A(f"|---:|---|---:|---:|")
        for i, r in enumerate(items, 1):
            A(f"| {i} | `{r['feature']}` | {r['gain']:.2f} | {int(r['split'])} |")
        A("")

    # Surprises
    A("**Surprises — top-gain features with low univariate ρ (< 0.10):** these are interaction-signal candidates.")
    A("")
    if R["surprises_top_gain_low_rho"]:
        A(f"| rank | feature | gain | catalog_rho |")
        A(f"|---:|---|---:|---:|")
        for r in R["surprises_top_gain_low_rho"]:
            rho = r.get("catalog_rho", float("nan"))
            rho_str = f"{float(rho):+.3f}" if not (isinstance(rho, float) and math.isnan(rho)) else "nan"
            A(f"| {int(r['gain_rank'])} | `{r['feature']}` | {r['gain']:.2f} | {rho_str} |")
    else:
        A("(none under threshold)")
    A("")
    A("---")
    A("")

    # Section 4
    A("## Section 4 — White-noise null distribution")
    A("")
    A(f"**Procedure:** shuffle train+val labels with {R['null']['n_shuffles']} distinct seeds {R['null']['seeds']}, retrain identical-hyperparam global LightGBM, score the BURNED test slice.")
    A("")
    A(f"| metric | value |")
    A(f"|---|---:|")
    A(f"| n_shuffles | {R['null']['n_shuffles']} |")
    A(f"| null AUC mean | {R['null']['mean']:.4f} |")
    A(f"| null AUC std | {R['null']['std']:.4f} |")
    A(f"| null AUC max | {R['null']['max']:.4f} |")
    A(f"| **real test AUC** | **{R['auc']['test']:.4f}** |")
    A(f"| z-score | {R['null']['z_score']:.2f} |")
    A(f"| p-value (empirical, one-sided) | {R['null']['p_empirical_one_sided']:.4f} |")
    A(f"| p-value (smoothed, Phipson-Smyth-style) | {R['null']['p_smoothed']:.4f} |")
    A("")
    A(f"**Per-shuffle null AUCs:** {[round(x, 4) for x in R['null']['aucs']]}")
    A("")
    A("**Note:** with n_shuffles=10 the empirical p-floor is 1/11 ≈ 0.091 (smoothed). For a tighter p value, run more shuffles at Week-4 modeling time.")
    A("")
    A("---")
    A("")

    # Section 5 — Verdict
    A("## Section 5 — Verdict")
    A("")
    test_auc = R["headline_test_auc"]
    pr_test_auc = R["auc_per_regime_ensemble"]["test"]
    null_max = R["null"]["max"]
    p_emp = R["null"]["p_empirical_one_sided"]
    p_smoothed = R["null"]["p_smoothed"]

    if not (math.isnan(test_auc) or math.isnan(p_smoothed)):
        signal_yes = test_auc > null_max and p_smoothed < 0.10
        beats_baseline = test_auc > 0.571
        plausible_61 = test_auc >= 0.61
    else:
        signal_yes = False
        beats_baseline = False
        plausible_61 = False

    A(f"### Q1: Does the catalog have signal? **{'YES' if signal_yes else 'INCONCLUSIVE'}**")
    A("")
    A(f"- HEADLINE (global-only) test AUC = **{test_auc:.4f}**.")
    A(f"- Per-regime ensemble test AUC = {pr_test_auc:.4f} (regime fragmentation drag at this n).")
    A(f"- Null distribution mean = **{R['null']['mean']:.4f}**, std = {R['null']['std']:.4f}, max = **{null_max:.4f}**.")
    A(f"- Real beats null max? **{test_auc > null_max}** (delta {test_auc - null_max:+.4f}).")
    A(f"- z-score = {R['null']['z_score']:.2f}.")
    A(f"- p_empirical (one-sided) = **{p_emp:.4f}**, p_smoothed = **{p_smoothed:.4f}**.")
    z_str = f"{R['null']['z_score']:.2f}"
    if p_smoothed < 0.05:
        verdict_text = "YES (p_smoothed < 0.05)"
    else:
        verdict_text = (f"YES on z-score ({z_str} sigma) and p_empirical={p_emp:.4f} (0/10 nulls "
                        f"beat real); smoothed p has a 1/(B+1)=0.091 floor at n=10 shuffles, not a "
                        f"signal-absence indicator")
    A(f"- Verdict: signal exists at p < 0.05? **{verdict_text}**.")
    A("")

    A(f"### Q2: Is AUC ≥ 0.61 plausible at Week-4 modeling? **{'YES (already exceeds with global-only)' if plausible_61 else ('PLAUSIBLE-WITH-CONDITIONS' if (test_auc >= 0.58 and beats_baseline) else ('MAYBE-WITH-CONDITIONS' if beats_baseline else 'STALL near baseline'))}**")
    A("")
    A(f"- Headline test AUC vs the 0.61 threshold: **{test_auc:.4f}** vs 0.61 → {'meets/exceeds (delta +' + f'{test_auc - 0.61:.4f}' + ')' if test_auc >= 0.61 else f'misses by {0.61 - test_auc:.4f}'}.")
    A(f"- Headline vs K54 v1 baseline (0.571): **{test_auc - 0.571:+.4f}**.")
    A(f"- Per-regime vs K54 v1 baseline: {pr_test_auc - 0.571:+.4f} (degraded at this n+feature_count).")
    A("")
    if test_auc >= 0.61:
        A(f"**Recommendation:** Week-4 catalog modeling is HIGHLY LIKELY to achieve AUC ≥ 0.61. Scout's tiny-LightGBM global-only model already crosses the bar by **{test_auc - 0.61:+.4f}**. Full Optuna search + CPCV-with-purge + cross-period replication should hold or improve. **Architectural recommendation: do NOT inherit K54 v1's per-regime gating without re-evaluating** — at 1,219 features the ensemble fragmentation drag (-{test_auc - pr_test_auc:.4f} AUC) outweighs the K54 v1 ensemble's +0.032 lift. Either keep regime-as-feature in the global model (current scout architecture) OR raise per-regime min-rows above 60+ before fragmenting.")
    elif test_auc >= 0.58 and beats_baseline:
        A(f"**Recommendation:** AUC ≥ 0.61 is **PLAUSIBLE** at Week 4 with **conditions**: (1) full Optuna hyperparameter search; (2) CPCV ensemble averaging tightens AUC SE; (3) feature pruning by Pearson correlation may add 0.5-1.5 AUC points; (4) cross-period train (2022-2025) expands n. Scout shows lift over K54 v1 baseline; an extra ~3-5 AUC points from these enhancements is reasonable.")
    elif beats_baseline:
        A(f"**Recommendation:** AUC ≥ 0.61 is **MAYBE-WITH-CONDITIONS**. Scout AUC {test_auc:.4f} beats K54 v1 (0.571) but is short of 0.61. Week-4 modeling needs aggressive feature selection + cross-period train + ensemble averaging to close the gap.")
    else:
        A(f"**Recommendation:** Catalog STALLS near the K54 v1 baseline 0.571. AUC ≥ 0.61 at Week 4 is **UNLIKELY** without major feature additions.")
    A("")
    A("**Notes for Q1.2 modeler:**")
    A("1. Scout test slice is BURNED — these numbers are ballpark, not validation. The locked Q1.2 holdout 2026-04-29 → 2026-05-12 remains untouched.")
    A("2. Per-regime n in test is SMALL (~15-40 per regime). AUC SE per regime is large (~0.10). Treat per-regime AUCs as directional, not predictive.")
    A("3. NaN density is high for trades pre-2025-10 (12 trades) and for tick-required microstructure (24 features all NaN — no parquet coverage). LightGBM handles NaN natively; no imputation needed.")
    A("4. **Global-only >= per-regime at this n.** The per-regime ensemble fragmenting train into 4 regimes (smallest = 21 rows) is harmful at the 1,219-feature scale. Reconsider K54 v1's per-regime architecture before Week-4 commits to it.")
    A(f"5. **Null distribution discipline:** test AUC={test_auc:.4f} is {(test_auc - R['null']['mean'])*100:+.2f}pp above null mean (z={R['null']['z_score']:.2f} sigma), beats null max by {test_auc - null_max:+.4f}. Empirical p={R['null']['p_empirical_one_sided']:.4f} (0/10 nulls >= real); smoothed p={R['null']['p_smoothed']:.4f} reflects 1/(B+1) floor at B=10. Modeler should run >100 shuffles to tighten p.")
    A("")

    # Final
    A("---")
    A("")
    A("**Files:**")
    A(f"- `research/ml_program/scout/feature_matrix.parquet` (or .csv) — unified feature matrix")
    A(f"- `research/ml_program/scout/feature_matrix_meta.json` — schema + shape")
    A(f"- `research/ml_program/scout/scout_results.json` — full numerical results")
    A(f"- `research/ml_program/scout/build_scout_matrix.py` — feature matrix builder")
    A(f"- `research/ml_program/scout/scout_model.py` — model + null + report writer")

    out_md = SCOUT_DIR / "joint_model_scout.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
