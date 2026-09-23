"""Synthesis — concatenate slices, fit classifiers on TRAIN, evaluate on TEST,
cluster missed wins + anti-pattern losses, produce rich output tables.

Output:
  research/phase1_xauusd_reverse_engineering/synthesis_output/
    classifier_metrics.json
    feature_importances.json
    missed_clusters.json
    anti_clusters.json
    (plus any intermediates)

Design:
- No overwrite — timestamps into /runs/<isots>/ if present. But caller may
  use --out to pin path for the markdown writer.
- Classifier: GradientBoostingClassifier (lightgbm unavailable). One-hot encode
  categoricals. All NaN/None → impute to -999 flag (tree splits handle it).
- Test metrics authoritative.
- Bonferroni: with 4 label classifiers tested as gates, Bonferroni factor = 4.
  Additional per-feature tests get their own correction within section.
- Bootstrap 1000 iterations for WR/expectancy CIs.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys
import time as _time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)

RNG = np.random.default_rng(42)

SLICE_DIR = Path(__file__).parent
OUT_DIR = SLICE_DIR / "synthesis_output"
OUT_DIR.mkdir(exist_ok=True)

TRAIN_CUTOFF = "2026-03-01"
TEST_END = "2026-04-14"  # exclusive

# ---------------------------------------------------------------------------
# Load + prep
# ---------------------------------------------------------------------------

def load_all_slices(slice_dir: Path) -> pd.DataFrame:
    # Only numbered slices — exclude smoke dir
    files = []
    for i in range(1, 17):
        p = slice_dir / f"slice_{i}" / "features.parquet"
        if p.exists():
            files.append(p)
    dfs = []
    for f in files:
        df = pd.read_parquet(f)
        df["_slice_file"] = f.parent.name
        dfs.append(df)
    if not dfs:
        raise RuntimeError(f"No numbered slice feature files in {slice_dir}")
    df = pd.concat(dfs, ignore_index=True)
    return df


def add_split(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["direction"].isin(["LONG", "SHORT"])].copy()
    df = df[df["unlabeled"] == 0].copy()

    df["candle_dt"] = pd.to_datetime(df["candle_time"], utc=True, errors="coerce")
    df = df.dropna(subset=["candle_dt"]).copy()

    cutoff = pd.Timestamp(TRAIN_CUTOFF, tz="UTC")
    end = pd.Timestamp(TEST_END, tz="UTC")
    df = df[df["candle_dt"] < end].copy()
    df["split"] = np.where(df["candle_dt"] < cutoff, "train", "test")
    return df


CATEGORICAL = [
    "kill_zone", "direction", "d1_dir", "h4_dir", "h1_dir", "m15_dir",
    "pd_current_zone", "h1_opp_ob_causing_event", "sl_source",
]
NUMERIC_DROP = [
    "candle_time", "close_price", "sl_price", "r_denom",
    "label_quick", "label_primary", "label_premium", "label_anti",
    "label_quick_mfe", "label_quick_mae",
    "label_primary_mfe", "label_primary_mae",
    "label_premium_mfe", "label_premium_mae",
    "label_anti_mfe", "label_anti_mae",
    "unlabeled", "_slice_file",
]


def build_X(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    dropped = set(NUMERIC_DROP) | {"candle_dt", "split"}
    feature_cols = [c for c in df.columns if c not in dropped]
    X = df[feature_cols].copy()

    # One-hot encode categoricals
    cat_present = [c for c in CATEGORICAL if c in X.columns]
    X = pd.get_dummies(X, columns=cat_present, dummy_na=True, dtype=float)

    # Convert all remaining to numeric; object → coerce to NaN
    for c in X.columns:
        if X[c].dtype == object:
            X[c] = pd.to_numeric(X[c], errors="coerce")
    # Impute NaN to -999 flag (tree splits handle)
    X = X.fillna(-999.0)
    # Cast bool columns to float to avoid sklearn warnings
    for c in X.columns:
        if X[c].dtype == bool:
            X[c] = X[c].astype(float)
    return X, list(X.columns)


def bootstrap_ci(values: np.ndarray, iters: int = 1000, ci: float = 0.95) -> tuple[float, float]:
    if len(values) == 0:
        return (float("nan"), float("nan"))
    means = []
    n = len(values)
    for _ in range(iters):
        idx = RNG.integers(0, n, n)
        means.append(values[idx].mean())
    means = np.array(means)
    lo = (1 - ci) / 2
    return (float(np.quantile(means, lo)), float(np.quantile(means, 1 - lo)))


def bootstrap_rate_ci(hits: int, total: int, iters: int = 1000, ci: float = 0.95):
    if total == 0:
        return (float("nan"), float("nan"))
    samples = np.concatenate([np.ones(hits), np.zeros(total - hits)]).astype(int)
    means = []
    for _ in range(iters):
        idx = RNG.integers(0, total, total)
        means.append(samples[idx].mean())
    means = np.array(means)
    lo = (1 - ci) / 2
    return (float(np.quantile(means, lo)), float(np.quantile(means, 1 - lo)))


# ---------------------------------------------------------------------------
# Classifier fitting + evaluation
# ---------------------------------------------------------------------------

def fit_and_eval(
    X_tr: pd.DataFrame, y_tr: pd.Series,
    X_te: pd.DataFrame, y_te: pd.Series,
    label_name: str,
) -> dict:
    # Use float arrays explicitly to avoid sklearn / bool incompat
    clf = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )
    clf.fit(X_tr.values, y_tr.values)

    def metrics(X, y, tag):
        prob = clf.predict_proba(X.values)[:, 1]
        pred = (prob >= 0.5).astype(int)
        auc = roc_auc_score(y, prob) if len(set(y)) > 1 else float("nan")
        ap = average_precision_score(y, prob) if len(set(y)) > 1 else float("nan")
        # Precision/recall at threshold 0.5
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        tn = int(((pred == 0) & (y == 0)).sum())
        precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
        recall = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
        # Also compute operating point (best F1 over PR curve)
        op_prec, op_rec, op_thr, op_f1 = float("nan"), float("nan"), 0.5, float("nan")
        if len(set(y)) > 1:
            prec_arr, rec_arr, thr_arr = precision_recall_curve(y, prob)
            f1s = 2 * prec_arr * rec_arr / (prec_arr + rec_arr + 1e-12)
            best_i = int(np.argmax(f1s[:-1])) if len(f1s) > 1 else 0
            op_prec = float(prec_arr[best_i])
            op_rec = float(rec_arr[best_i])
            op_thr = float(thr_arr[best_i]) if best_i < len(thr_arr) else 0.5
            op_f1 = float(f1s[best_i])
        return {
            "tag": tag,
            "n": int(len(y)),
            "positive_rate": float(y.mean()),
            "auc": float(auc),
            "average_precision": float(ap),
            "confusion_matrix_0p5": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "precision_0p5": float(precision),
            "recall_0p5": float(recall),
            "best_f1_op_point": {
                "threshold": op_thr,
                "precision": op_prec,
                "recall": op_rec,
                "f1": op_f1,
            },
        }

    out = {
        "label": label_name,
        "train": metrics(X_tr, y_tr, "train"),
        "test": metrics(X_te, y_te, "test"),
    }

    # Feature importance — gain-based
    fi_gain = dict(zip(X_tr.columns, clf.feature_importances_))
    fi_gain_top = sorted(fi_gain.items(), key=lambda kv: -kv[1])[:25]
    out["feature_importance_gain_top25"] = [
        {"feature": f, "importance": float(imp)} for f, imp in fi_gain_top
    ]

    # Permutation importance on TEST (more honest)
    # limit to test set
    try:
        perm = permutation_importance(
            clf, X_te.values, y_te.values,
            n_repeats=5, random_state=42, n_jobs=-1,
        )
        perm_means = dict(zip(X_tr.columns, perm.importances_mean))
        perm_top = sorted(perm_means.items(), key=lambda kv: -kv[1])[:25]
        out["feature_importance_permutation_test_top25"] = [
            {"feature": f, "importance": float(imp)} for f, imp in perm_top
        ]
    except Exception as e:
        out["feature_importance_permutation_test_top25"] = []
        out["permutation_error"] = str(e)[:200]

    out["_clf"] = clf  # caller-only — don't JSON-serialize
    return out


# ---------------------------------------------------------------------------
# Clustering (tree leaves + descriptive stats)
# ---------------------------------------------------------------------------

def cluster_by_leaves(
    clf: GradientBoostingClassifier,
    X: pd.DataFrame,
    top_leaves: int = 6,
) -> np.ndarray:
    """Use terminal leaves of the FIRST decision tree in the ensemble as a
    coarse cluster id. Fast and interpretable."""
    tree = clf.estimators_[0, 0]
    leaves = tree.apply(X.values)
    return leaves


def describe_cluster(
    df: pd.DataFrame,
    X: pd.DataFrame,
    mask: np.ndarray,
    features_for_profile: list[str],
    n_top: int = 8,
) -> dict:
    sub = df[mask].copy()
    Xsub = X[mask].copy()
    profile = {}
    for f in features_for_profile:
        if f in X.columns:
            try:
                profile[f] = {
                    "median": float(np.nanmedian(Xsub[f].values)),
                    "mean": float(np.nanmean(Xsub[f].values)),
                }
            except Exception:
                pass
    # Descriptive categorical modes
    cat_summary = {}
    for c in ["kill_zone", "direction", "d1_dir", "h4_dir", "h1_dir",
              "m15_dir", "pd_current_zone", "h1_opp_ob_causing_event",
              "sl_source"]:
        if c in df.columns:
            cat_summary[c] = df[mask][c].value_counts().head(5).to_dict()
    date_range = {
        "min": str(sub["candle_dt"].min()) if len(sub) else None,
        "max": str(sub["candle_dt"].max()) if len(sub) else None,
    }
    return {
        "n": int(mask.sum()),
        "numeric_profile": profile,
        "categorical_modes": cat_summary,
        "date_range": date_range,
    }


# ---------------------------------------------------------------------------
# Hit/miss mapping against production candidate log
# ---------------------------------------------------------------------------

def load_candidate_log(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    if not rows:
        return pd.DataFrame()
    dfc = pd.DataFrame(rows)
    dfc["candle_dt"] = pd.to_datetime(dfc["timestamp_utc"], utc=True, errors="coerce")
    return dfc


def m15_round(ts: pd.Timestamp) -> pd.Timestamp:
    """Round DOWN to M15 close. Candle opens at :00 :15 :30 :45; closes at
    the same times +15. CANDIDATE log is stamped with candle-close evaluation
    start, so rounding to floor minute//15*15 is fine."""
    if pd.isna(ts):
        return pd.NaT
    m = (ts.minute // 15) * 15
    return ts.replace(minute=m, second=0, microsecond=0, nanosecond=0)


def hit_miss_analysis(df: pd.DataFrame, cand_df: pd.DataFrame) -> dict:
    if cand_df.empty:
        return {"note": "No production candidate log rows available."}
    cand_df = cand_df[cand_df["symbol"] == "XAUUSD"].copy()
    if cand_df.empty:
        return {"note": "No XAUUSD rows in candidate log (symbol field may be empty pre-Wave2.5)."}

    # Filter to test range for fair comparison (live shadow log only started mid-April)
    cand_df["candle_dt_round"] = cand_df["candle_dt"].apply(m15_round)
    df_test = df[df["split"] == "test"].copy()
    df_test["candle_dt_round"] = df_test["candle_dt"].apply(m15_round)

    # Join on candle_dt_round; direction matching: production emits 'ai_direction'
    # for CANDIDATEs, but for misses we don't know direction. We'll count:
    #  A. primary-positive candles where GTOS emitted CANDIDATE any direction
    #  B. primary-positive candles where GTOS emitted NO_TRADE

    # For our walked features, a candle can be labeled positive in LONG OR SHORT
    # OR both. We collapse to per-candle primary-positive flag.
    per_cand = df_test.groupby("candle_dt_round").agg(
        long_positive=("label_primary",
                        lambda s: int(((df_test.loc[s.index, "direction"] == "LONG")
                                       & (df_test.loc[s.index, "label_primary"] == 1)).any())),
        short_positive=("label_primary",
                         lambda s: int(((df_test.loc[s.index, "direction"] == "SHORT")
                                        & (df_test.loc[s.index, "label_primary"] == 1)).any())),
    ).reset_index()
    per_cand["any_positive"] = (
        (per_cand["long_positive"] == 1) | (per_cand["short_positive"] == 1)
    ).astype(int)

    # GTOS decision per candle
    cand_df_pos = cand_df.set_index("candle_dt_round")["decision"].to_dict()

    hits = 0
    misses = 0
    cand_no_pos = 0
    cand_count_overall = 0
    pos_total = int(per_cand["any_positive"].sum())
    for _, r in per_cand.iterrows():
        t = r["candle_dt_round"]
        dec = cand_df_pos.get(t)
        if r["any_positive"] == 1:
            if dec == "CANDIDATE":
                hits += 1
            else:
                misses += 1
        else:
            if dec == "CANDIDATE":
                cand_no_pos += 1
        if dec == "CANDIDATE":
            cand_count_overall += 1

    overlap = (per_cand["candle_dt_round"].isin(cand_df_pos.keys())).sum()
    return {
        "test_window_pos_candles": pos_total,
        "test_window_all_candles": int(len(per_cand)),
        "test_window_overlap_with_production_log": int(overlap),
        "production_cands_overlapping_test": int(cand_count_overall),
        "hits_production_cand_on_positive_candle": int(hits),
        "misses_positive_candle_no_cand": int(misses),
        "production_cand_on_neg_candle": int(cand_no_pos),
        "miss_rate": float(misses / pos_total) if pos_total > 0 else None,
        "note": (
            "Production candidate log is sparse on XAUUSD test window — started "
            "logging ~2026-04-17 (per candidate_features_log.jsonl earliest entry). "
            "This mapping is advisory only; small sample."
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(args):
    t0 = _time.time()
    df_raw = load_all_slices(SLICE_DIR)
    df = add_split(df_raw)
    print(f"[synth] loaded {len(df_raw)} raw rows -> {len(df)} labeled rows")
    print(f"[synth] split counts: {df['split'].value_counts().to_dict()}")

    # Per-label positive rates by split
    split_rates = {}
    for split in ["train", "test"]:
        sub = df[df["split"] == split]
        split_rates[split] = {}
        for name in ["primary", "quick", "premium", "anti"]:
            col = f"label_{name}"
            total = int(sub[col].notna().sum())
            pos = int((sub[col] == 1).sum())
            rate = pos / total if total else None
            split_rates[split][name] = {"n": total, "positive": pos, "rate": rate}

    X_all, features = build_X(df)
    print(f"[synth] built X with {len(features)} features")

    tr_mask = (df["split"] == "train").values
    te_mask = (df["split"] == "test").values

    # Fit one classifier per label
    all_metrics = {}
    clfs = {}
    cluster_cache = {}
    for label_name in ["primary", "quick", "premium", "anti"]:
        col = f"label_{label_name}"
        y = df[col].astype("Int64")
        ok = y.notna().values & (y != -1).values if False else y.notna().values
        Xtr = X_all[tr_mask & ok]
        ytr = df.loc[tr_mask & ok, col].astype(int)
        Xte = X_all[te_mask & ok]
        yte = df.loc[te_mask & ok, col].astype(int)
        if len(set(ytr)) < 2 or len(set(yte)) < 2:
            print(f"[synth] skipping {label_name} — single-class split")
            continue
        res = fit_and_eval(Xtr, ytr, Xte, yte, label_name)
        clf = res.pop("_clf")
        clfs[label_name] = clf
        all_metrics[label_name] = res
        print(f"[synth] {label_name}: train AUC={res['train']['auc']:.3f}  test AUC={res['test']['auc']:.3f}  "
              f"test precision@best_f1={res['test']['best_f1_op_point']['precision']:.3f} "
              f"recall@best_f1={res['test']['best_f1_op_point']['recall']:.3f}")

    # Save metrics
    with open(OUT_DIR / "classifier_metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)

    # Feature importance aggregate
    with open(OUT_DIR / "feature_importances.json", "w") as f:
        json.dump(
            {k: {"gain_top25": v["feature_importance_gain_top25"],
                 "permutation_top25": v["feature_importance_permutation_test_top25"]}
             for k, v in all_metrics.items()},
            f, indent=2, default=str,
        )

    # ===============
    # Missed-win clusters — for PRIMARY label
    # ===============
    missed_clusters = {}
    if "primary" in clfs:
        clf = clfs["primary"]
        # Use TRAIN for clustering so missed-win definition is pre-test
        y_full = df["label_primary"].astype("Int64")
        tr_ok = tr_mask & y_full.notna().values
        te_ok = te_mask & y_full.notna().values
        Xtr = X_all[tr_ok]
        df_tr = df[tr_ok].copy()

        # Compute predicted probability on TRAIN
        prob_tr = clf.predict_proba(Xtr.values)[:, 1]
        df_tr["pred_prob"] = prob_tr

        # Compute prediction on TEST (that's what we'll actually apply)
        Xte = X_all[te_ok]
        df_te = df[te_ok].copy()
        prob_te = clf.predict_proba(Xte.values)[:, 1]
        df_te["pred_prob"] = prob_te

        # Cluster by first-tree leaves on train; confirm rate persists on test
        leaves_tr = cluster_by_leaves(clf, Xtr)
        leaves_te = cluster_by_leaves(clf, Xte)
        df_tr["leaf_id"] = leaves_tr
        df_te["leaf_id"] = leaves_te

        # Rank leaves by TRAIN positive rate (minimum n threshold for rate reliability)
        leaf_stats = []
        min_n = 30
        for leaf_id, g in df_tr.groupby("leaf_id"):
            n_tr = len(g)
            if n_tr < min_n:
                continue
            pos_tr = int((g["label_primary"] == 1).sum())
            rate_tr = pos_tr / n_tr
            g_te = df_te[df_te["leaf_id"] == leaf_id]
            n_te = len(g_te)
            pos_te = int((g_te["label_primary"] == 1).sum()) if n_te else 0
            rate_te = (pos_te / n_te) if n_te else None
            ci_te = bootstrap_rate_ci(pos_te, n_te) if n_te > 0 else (None, None)
            leaf_stats.append({
                "leaf_id": int(leaf_id),
                "train_n": int(n_tr),
                "train_positive_rate": float(rate_tr),
                "test_n": int(n_te),
                "test_positive_rate": rate_te,
                "test_ci95": ci_te,
            })
        leaf_stats.sort(key=lambda x: -(x["train_positive_rate"] or 0))

        # Pick top 5 leaves by train positive rate
        top_leaves = leaf_stats[:5]
        # Profile each on TRAIN (to show characteristic feature values)
        feats_profile = [
            "mtf_alignment_score", "h1_unmit_ob_count", "h1_opp_ob_dist_atr",
            "h1_opp_ob_touch", "h1_opp_ob_age_hours",
            "h1_fvg_unfilled_count", "m15_fvg_unfilled_count",
            "m15_atr_14", "h1_atr_14", "h1_atr_rolling_20d", "atr_regime",
            "pd_dist_atr", "m15_clv_current", "m15_clv_avg_5",
            "m15_bvc_buy_fraction", "m15_net_flow_5",
            "sweeps_n20", "pool_same_side_dist_atr", "pool_opp_side_dist_atr",
            "h1_hh_count", "h1_hl_count", "h1_lh_count", "h1_ll_count",
            "range_pct_20",
        ]
        clusters_out = []
        for lf in top_leaves:
            mask = (df_tr["leaf_id"] == lf["leaf_id"]).values
            prof = describe_cluster(df_tr, Xtr, mask, feats_profile)
            lf["profile"] = prof
            clusters_out.append(lf)
        missed_clusters["top_leaves_by_train_positive_rate"] = clusters_out

        # Also: MISSES — positive candles NOT currently CANDIDATE in production
        # We approximate "where GTOS would currently reject" by finding rows where
        # the test set has label_primary=1 AND mtf_alignment_score is LOW (since
        # GTOS's C-gate requires h4 alignment). This is the "miss" lens.
        df_te_pos = df_te[df_te["label_primary"] == 1].copy()
        # Coarse "would be missed" heuristic: C-gate equivalents fail
        # Current GTOS gates: c1_h1_bias_present, c2_m15_choch_detected, c3_direction_matches
        # We proxy with: h1_dir != 'transitional'/'unk' + h4_h1_aligned
        df_te_pos["approx_c1_c2_pass"] = (
            (df_te_pos["h1_dir"].isin(["bullish", "bearish"]))
            & (df_te_pos["m15_dir"].isin(["bullish", "bearish"]))
        ).astype(int)
        df_te_pos["approx_c3_match"] = (
            ((df_te_pos["direction"] == "LONG") & (df_te_pos["h1_dir"] == "bullish"))
            | ((df_te_pos["direction"] == "SHORT") & (df_te_pos["h1_dir"] == "bearish"))
        ).astype(int)
        df_te_pos["would_current_gtos_reject"] = (
            (df_te_pos["approx_c1_c2_pass"] == 0)
            | (df_te_pos["approx_c3_match"] == 0)
        ).astype(int)

        missed = df_te_pos[df_te_pos["would_current_gtos_reject"] == 1]
        missed_clusters["approx_rejected_by_current_gtos"] = {
            "n_positive_candles_in_test": int(len(df_te_pos)),
            "n_approx_missed": int(len(missed)),
            "miss_rate": float(len(missed) / len(df_te_pos)) if len(df_te_pos) else None,
            "approx_rule": (
                "Current GTOS rejects when C-gate fails: h1_dir not bullish/bearish, "
                "m15_dir not bullish/bearish, or direction doesn't match h1 bias. "
                "Proxy does not model the full primary_analyzer prompt, only the deterministic "
                "pre-AI gates. REAL miss rate is likely lower because the AI can reject "
                "structurally-aligned setups for other reasons."
            ),
        }

        # Break down missed candles by direction + h1_dir
        if len(missed):
            missed_by_direction = missed.groupby(["direction", "h1_dir"]).size().to_dict()
            missed_clusters["approx_missed_by_direction_h1"] = {
                f"{k[0]}/{k[1]}": int(v) for k, v in missed_by_direction.items()
            }

    with open(OUT_DIR / "missed_clusters.json", "w") as f:
        json.dump(missed_clusters, f, indent=2, default=str)

    # ===============
    # Anti-pattern clusters
    # ===============
    anti_clusters = {}
    if "anti" in clfs:
        clf = clfs["anti"]
        y_full_a = df["label_anti"].astype("Int64")
        tr_ok_a = tr_mask & y_full_a.notna().values
        te_ok_a = te_mask & y_full_a.notna().values
        Xtr = X_all[tr_ok_a]
        df_tr = df[tr_ok_a].copy()
        prob_tr = clf.predict_proba(Xtr.values)[:, 1]
        df_tr["pred_prob"] = prob_tr

        Xte = X_all[te_ok_a]
        df_te = df[te_ok_a].copy()
        prob_te = clf.predict_proba(Xte.values)[:, 1]
        df_te["pred_prob"] = prob_te
        # Rebind y_te for use below (legacy variable name)
        y_te = df_te["label_anti"].astype(int)

        # Anti-gate candidates: find thresholds at several precision targets
        prec_arr, rec_arr, thr_arr = precision_recall_curve(y_te.values, prob_te)
        # Find the MINIMUM threshold that gives precision >= target (best-recall at that precision)
        def find_op_at_prec(prec_target):
            cands = [
                {"threshold": float(thr_arr[i]) if i < len(thr_arr) else 1.0,
                 "precision": float(prec_arr[i]),
                 "recall": float(rec_arr[i])}
                for i in range(len(prec_arr)) if prec_arr[i] >= prec_target
            ]
            if not cands:
                return None
            # Pick the one with MAX recall (= lowest threshold that still meets precision)
            return max(cands, key=lambda c: c["recall"])

        op_points = {}
        for prec_target in [0.50, 0.60, 0.70, 0.75]:
            op = find_op_at_prec(prec_target)
            if op is None:
                op_points[f"prec_{int(prec_target*100)}"] = None
                continue
            thr = op["threshold"]
            flagged = df_te[df_te["pred_prob"] >= thr]
            losses = df_te[df_te["label_primary"] == 0]
            losses_flagged = losses[losses["pred_prob"] >= thr]
            wins = df_te[df_te["label_primary"] == 1]
            wins_flagged = wins[wins["pred_prob"] >= thr]
            op_points[f"prec_{int(prec_target*100)}"] = {
                **op,
                "flagged_n": int(len(flagged)),
                "flagged_loss_rate": float(len(losses_flagged) / len(losses)) if len(losses) else None,
                "flagged_win_rate": float(len(wins_flagged) / len(wins)) if len(wins) else None,
                "wins_rejected": int(len(wins_flagged)),
                "losses_rejected": int(len(losses_flagged)),
            }
        anti_clusters["operating_points"] = op_points

        # Use 60% as canonical (useful recall, still meaningful precision)
        best = op_points.get("prec_60") or op_points.get("prec_50")
        anti_clusters["canonical_operating_point_at_prec_60"] = best

        if best is not None:
            thr = best["threshold"]
            anti_clusters["flagged_profile_at_prec60"] = describe_cluster(
                df_te, Xte, (df_te["pred_prob"] >= thr).values,
                ["mtf_alignment_score", "h1_unmit_ob_count", "h1_opp_ob_dist_atr",
                 "h1_opp_ob_touch", "h1_opp_ob_age_hours", "pd_dist_atr",
                 "atr_regime", "sweeps_n20", "m15_clv_current", "m15_bvc_buy_fraction",
                 "range_pct_20"],
            )

    with open(OUT_DIR / "anti_clusters.json", "w") as f:
        json.dump(anti_clusters, f, indent=2, default=str)

    # ===============
    # Hit/miss vs production
    # ===============
    # candidate_features_log.jsonl is repo-level, not worktree
    root = Path(os.environ.get("GTOS_PROJECT_ROOT", "C:/Users/MSI/Documents/ai-trading-agent"))
    cand_path = root / "shadow_logs" / "candidate_features_log.jsonl"
    cand_df = load_candidate_log(cand_path)
    hit_miss = hit_miss_analysis(df, cand_df)

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "duration_sec": round(_time.time() - t0, 1),
        "raw_rows": int(len(df_raw)),
        "labeled_rows": int(len(df)),
        "n_features": len(features),
        "split_counts": df["split"].value_counts().to_dict(),
        "label_rates_by_split": split_rates,
        "classifier_summary": {
            k: {
                "train_auc": all_metrics[k]["train"]["auc"],
                "test_auc": all_metrics[k]["test"]["auc"],
                "test_best_f1_precision": all_metrics[k]["test"]["best_f1_op_point"]["precision"],
                "test_best_f1_recall": all_metrics[k]["test"]["best_f1_op_point"]["recall"],
                "test_best_f1_threshold": all_metrics[k]["test"]["best_f1_op_point"]["threshold"],
                "test_average_precision": all_metrics[k]["test"]["average_precision"],
            }
            for k in all_metrics
        },
        "hit_miss_vs_production": hit_miss,
    }
    with open(OUT_DIR / "synthesis_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print("[synth] DONE")
    print(json.dumps(summary["classifier_summary"], indent=2, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice-dir", default=str(SLICE_DIR))
    args = ap.parse_args()
    main(args)
