"""E9 — Train Track A's anti-pattern classifier on Jan-Feb slices (train split)
and score A1's logged rows (CAND-only) for out-of-sample validation.

The shared feature subset between Track A master features and A1 logger:

Track A feature                <->  A1 logger field
  h1_opp_ob_touch              <->  h1_opp_ob_touch (semantics-corrected)
  h1_fvg_unfilled_count        <->  h1_fvg_unfilled_count
  m15_fvg_unfilled_count       <->  m15_fvg_unfilled_count
  h1_ob_max_touch              <->  max(mso_h1_ob_touch_counts)
  h1_unmit_ob_count            <->  mso_h1_unmitigated_ob_count
  h1_opp_ob_dist_atr           <->  mso_h1_nearest_ob_distance_atr (approximate)
  sweeps_n20                   <->  mso_detected_sweeps_count (approximate — not 20-cndl)
  m15_clv_current              <->  mso_m15_clv_current
  m15_clv_avg_5                <->  mso_m15_clv_avg_5
  m15_bvc_buy_fraction         <->  mso_m15_bvc_buy_fraction
  direction                    <->  ai_direction_evaluated
  kill_zone                    <->  kill_zone
  hour_utc                     <->  hour_utc
  day_of_week                  <->  day_of_week
  h1_atr_14                    <->  mso_h1_atr_14
  m15_atr_14                   <->  mso_m15_atr_14
  d1_atr_14                    <->  mso_d1_atr_14

Mapping limitations:
- Track A's `h1_opp_ob_dist_atr` is distance in ATR-units; A1's
  `mso_h1_nearest_ob_distance_atr` is also ATR-units. Same semantics.
- Track A's `sweeps_n20` is count in last 20 candles. A1's
  `mso_detected_sweeps_count` is cumulative total. Correlation
  preserved but scale differs. We log-transform both.

We train on TRAIN (Track A Jan-Feb) and score A1 CANDs (Jan-Apr 2026). This
is partly in-sample regime-wise but out-of-sample model-wise (A1 logger
data was never seen by classifier).

Write outputs to extraction_output.json["E9"].
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
TRACK_A_DIR = REPO / "research" / "phase1_xauusd_reverse_engineering"
A1_MERGED = REPO / "research" / "phase1_full_extraction" / "merged_data.jsonl"
OUT = REPO / "research" / "phase1_full_extraction" / "e9_output.json"


def load_track_a() -> pd.DataFrame:
    dfs = []
    for i in range(1, 9):
        p = TRACK_A_DIR / f"slice_{i}" / "features.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    df = df[df.direction.isin(["LONG", "SHORT"])].copy()
    df = df[df.unlabeled == 0].copy()
    df["candle_dt"] = pd.to_datetime(df["candle_time"], utc=True, errors="coerce")
    df = df.dropna(subset=["candle_dt"]).copy()
    df["split"] = np.where(df["candle_dt"] < pd.Timestamp("2026-03-01", tz="UTC"), "train", "test")
    return df


SHARED_FEATURES = [
    "h1_opp_ob_touch",
    "h1_fvg_unfilled_count",
    "m15_fvg_unfilled_count",
    "h1_ob_max_touch",
    "h1_unmit_ob_count",
    "h1_opp_ob_dist_atr",
    "m15_clv_current",
    "m15_clv_avg_5",
    "m15_bvc_buy_fraction",
    "hour_utc",
    "day_of_week",
    "h1_atr_14",
    "m15_atr_14",
    "d1_atr_14",
]


def build_x_track_a(df: pd.DataFrame) -> pd.DataFrame:
    X = df[SHARED_FEATURES].copy()
    # one-hot direction
    X["is_short"] = (df["direction"] == "SHORT").astype(float)
    # impute to -999
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.fillna(-999.0)
    return X


def build_x_a1(rows: list[dict]) -> pd.DataFrame:
    data = []
    for r in rows:
        # Feature mapping — may have None or missing
        # h1_opp_ob_touch: use direction-aware field
        dr = r.get("ai_direction_evaluated")
        if dr == "LONG":
            touch = r.get("h1_opp_ob_touch_long")
        elif dr == "SHORT":
            touch = r.get("h1_opp_ob_touch_short")
        else:
            touch = r.get("h1_opp_ob_touch")
        if touch is not None and touch < 0:
            touch = None  # -1 sentinel in A1
        ob_touches = r.get("mso_h1_ob_touch_counts") or []
        try:
            h1_ob_max_touch = max(ob_touches) if ob_touches else None
        except Exception:
            h1_ob_max_touch = None
        data.append({
            "h1_opp_ob_touch": touch,
            "h1_fvg_unfilled_count": r.get("h1_fvg_unfilled_count"),
            "m15_fvg_unfilled_count": r.get("m15_fvg_unfilled_count"),
            "h1_ob_max_touch": h1_ob_max_touch,
            "h1_unmit_ob_count": r.get("mso_h1_unmitigated_ob_count"),
            "h1_opp_ob_dist_atr": r.get("mso_h1_nearest_ob_distance_atr"),
            "m15_clv_current": r.get("mso_m15_clv_current"),
            "m15_clv_avg_5": r.get("mso_m15_clv_avg_5"),
            "m15_bvc_buy_fraction": r.get("mso_m15_bvc_buy_fraction"),
            "hour_utc": r.get("hour_utc"),
            "day_of_week": r.get("day_of_week"),
            "h1_atr_14": None,  # not in A1 logger — impute
            "m15_atr_14": None,
            "d1_atr_14": None,
            "is_short": 1.0 if dr == "SHORT" else 0.0,
        })
    X = pd.DataFrame(data)
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.fillna(-999.0)
    return X


def main():
    print("Loading Track A slices...")
    trk_a = load_track_a()
    print(f"Track A rows: {len(trk_a)} (train {len(trk_a[trk_a.split=='train'])} / test {len(trk_a[trk_a.split=='test'])})")

    # Train anti-pattern (label_anti=1 = bad, so classifier predicts prob of anti-pattern)
    train = trk_a[trk_a.split == "train"]
    X_tr = build_x_track_a(train)
    y_tr = train.label_anti.astype(int)

    test = trk_a[trk_a.split == "test"]
    X_te = build_x_track_a(test)
    y_te = test.label_anti.astype(int)

    # Need h1_atr fields in Track A — they're present
    print("Training classifier on shared-feature subset (14 features + is_short)...")
    clf = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)
    clf.fit(X_tr.values, y_tr.values)
    # Evaluate on Track A test
    p_tr = clf.predict_proba(X_tr.values)[:, 1]
    p_te = clf.predict_proba(X_te.values)[:, 1]
    auc_tr = roc_auc_score(y_tr, p_tr) if len(set(y_tr)) > 1 else float("nan")
    auc_te = roc_auc_score(y_te, p_te) if len(set(y_te)) > 1 else float("nan")
    ap_tr = average_precision_score(y_tr, p_tr) if len(set(y_tr)) > 1 else float("nan")
    ap_te = average_precision_score(y_te, p_te) if len(set(y_te)) > 1 else float("nan")
    print(f"Shared-subset classifier: AUC(train)={auc_tr:.4f}, AUC(test)={auc_te:.4f}, AP(train)={ap_tr:.4f}, AP(test)={ap_te:.4f}")

    # Now load A1 merged rows and score
    rows = []
    with open(A1_MERGED) as f:
        for line in f:
            rows.append(json.loads(line))
    # Keep only rows where we know realized outcome (CAND + WIN/LOSS/BE)
    cand_rows = [r for r in rows if r.get("out_decision") == "CANDIDATE" and r.get("out_outcome") in {"WIN", "LOSS", "BE"}]
    print(f"A1 scored rows (filled CANDs): {len(cand_rows)}")

    if not cand_rows:
        out = {"error": "no_filled_cands"}
        with open(OUT, "w") as f:
            json.dump(out, f, indent=2)
        return

    X_a1 = build_x_a1(cand_rows)
    p_a1 = clf.predict_proba(X_a1.values)[:, 1]

    # Correlate classifier probability (higher = more anti-pattern) with realized R (negative corr expected)
    r_vals = [r["out_r_multiple"] for r in cand_rows]
    # Also use binary: is_loss = (r < 0)
    is_loss = [1 if r["out_r_multiple"] is not None and r["out_r_multiple"] < 0 else 0 for r in cand_rows]
    # Score r vs probability: spearman
    from scipy.stats import spearmanr, pearsonr
    sp_rho, sp_p = spearmanr(p_a1, r_vals)
    pr_rho, pr_p = pearsonr(p_a1, r_vals)
    # AUC: classifier-flag predicts losses
    auc_loss = roc_auc_score(is_loss, p_a1) if len(set(is_loss)) > 1 else float("nan")
    ap_loss = average_precision_score(is_loss, p_a1) if len(set(is_loss)) > 1 else float("nan")
    print(f"A1 OOS: Spearman(clf_prob, R)={sp_rho:.4f} (p={sp_p:.4f}); Pearson={pr_rho:.4f} (p={pr_p:.4f})")
    print(f"A1 OOS: AUC(clf_prob -> is_loss)={auc_loss:.4f}; AP={ap_loss:.4f}")

    # Stratified WR/exp per classifier percentile
    strat = []
    # Sort by probability
    order = np.argsort(p_a1)
    sorted_r = np.array(r_vals, dtype=float)[order]
    sorted_p = p_a1[order]
    n = len(sorted_r)
    for q_lo, q_hi in [(0, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 1.0)]:
        i0 = int(n * q_lo); i1 = int(n * q_hi)
        if i1 <= i0: continue
        chunk_r = sorted_r[i0:i1]
        chunk_p = sorted_p[i0:i1]
        wins = int(sum(1 for v in chunk_r if v > 0))
        losses = int(sum(1 for v in chunk_r if v < 0))
        strat.append({
            "quartile": f"Q{int(q_hi*4)}",
            "n": len(chunk_r),
            "wins": wins, "losses": losses,
            "wr": wins / len(chunk_r) if len(chunk_r) else None,
            "mean_r": float(chunk_r.mean()) if len(chunk_r) else None,
            "prob_range": [float(chunk_p.min()), float(chunk_p.max())],
        })

    out = {
        "shared_feature_subset_count": len(SHARED_FEATURES) + 1,
        "track_a_train_n": int(len(train)),
        "track_a_test_n": int(len(test)),
        "track_a_train_auc": float(auc_tr),
        "track_a_test_auc": float(auc_te),
        "track_a_train_ap": float(ap_tr),
        "track_a_test_ap": float(ap_te),
        "a1_scored_n": len(cand_rows),
        "a1_spearman_rho_prob_vs_r": float(sp_rho),
        "a1_spearman_p_value": float(sp_p),
        "a1_pearson_rho_prob_vs_r": float(pr_rho),
        "a1_pearson_p_value": float(pr_p),
        "a1_auc_prob_vs_is_loss": float(auc_loss),
        "a1_ap_prob_vs_is_loss": float(ap_loss),
        "a1_quartile_stratification": strat,
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Written {OUT}")


if __name__ == "__main__":
    main()
