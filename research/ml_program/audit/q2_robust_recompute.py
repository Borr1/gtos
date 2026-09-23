#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recompute Q2 dropping low-cardinality (binary-OH) features that get inflated
correlations from cohort hour-imbalance.

Output appended to q2_correlation_summary.json:
  - "robust_n_pairs_above_0.7" (continuous-only)
  - "robust_n_pairs_above_0.9"
  - "robust_top_20_cross_family_pairs"
"""

from __future__ import annotations

import csv
import json
import sys
import time
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
AUDIT = REPO / "research" / "ml_program" / "audit"
SCRIPTS = REPO / "research" / "ml_program" / "scripts"
FEATURES = SCRIPTS / "features"

sys.path.insert(0, str(FEATURES))
sys.path.insert(0, str(REPO))

# Reuse helpers
from catalog_health_run import (  # noqa: E402
    load_ohlcv_pandas, load_ohlcv_dicts, find_anchor_idx, slice_until_pandas,
    TEST_INSTRUMENT,
)


def main():
    import pandas as pd

    # Load K54 v1 cohort
    k54v1_csv = REPO / ".claude" / "worktrees" / "agent-a01c00db65592ac2b" / "research" / "k54_ml_classifier_baseline" / "features.csv"
    rows = []
    with k54v1_csv.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    xau = [r for r in rows if r.get("symbol", "").upper() == "XAUUSD"]
    seen = set()
    deduped = []
    for r in xau:
        k = (r.get("date_iso", ""), r.get("hour_utc", ""), r.get("direction_long_short", ""))
        if k not in seen:
            seen.add(k)
            deduped.append(r)
    xau = deduped
    xau.sort(key=lambda r: r.get("date_iso", ""))

    target_n = 80
    if len(xau) >= target_n:
        step = max(1, len(xau) // target_n)
        sampled = xau[::step][:target_n]
    else:
        sampled = xau

    test_timestamps = []
    for r in sampled:
        date_iso = r.get("date_iso", "")
        ts = None
        try:
            if "T" in date_iso:
                s = date_iso.replace("Z", "+00:00")
                ts = datetime.fromisoformat(s)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            else:
                hr = int(r.get("hour_utc", "0") or "0")
                ts = datetime.strptime(date_iso, "%Y-%m-%d").replace(
                    hour=hr, tzinfo=timezone.utc
                )
        except (ValueError, TypeError):
            continue
        if ts > datetime(2026, 4, 28, 23, 59, 59, tzinfo=timezone.utc):
            continue
        test_timestamps.append(ts)

    test_timestamps = test_timestamps[:target_n]
    print(f"cohort: {len(test_timestamps)} timestamps")

    # Load OHLCV once
    df_m15 = load_ohlcv_pandas(TEST_INSTRUMENT, "M15")
    df_m1 = load_ohlcv_pandas(TEST_INSTRUMENT, "M1")
    df_h1 = load_ohlcv_pandas(TEST_INSTRUMENT, "H1")
    df_h4 = load_ohlcv_pandas(TEST_INSTRUMENT, "H4")
    candles_m15 = load_ohlcv_dicts(TEST_INSTRUMENT, "M15")
    candles_h1 = load_ohlcv_dicts(TEST_INSTRUMENT, "H1")
    candles_h4 = load_ohlcv_dicts(TEST_INSTRUMENT, "H4")
    candles_d1 = load_ohlcv_dicts(TEST_INSTRUMENT, "D1")

    import structure as structure_mod
    import volatility as volatility_mod
    import microstructure as microstructure_mod
    import time_session as time_session_mod
    import liquidity as liquidity_mod
    import regime as regime_mod
    regime_ctx = regime_mod.RegimeFeatureContext()

    feature_to_family = {}
    rows_out = []
    for i, ts in enumerate(test_timestamps):
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        if i % 10 == 0:
            print(f"  [{i+1}/{len(test_timestamps)}] {ts_str}")
        anchor_by_tf = {
            "M15": find_anchor_idx(candles_m15, ts_str),
            "H1": find_anchor_idx(candles_h1, ts_str),
            "H4": find_anchor_idx(candles_h4, ts_str),
        }
        if anchor_by_tf["M15"] < 0:
            continue
        ref_price = candles_m15[anchor_by_tf["M15"]]["close"]
        df_m15_s = slice_until_pandas(df_m15, ts)
        df_h1_s = slice_until_pandas(df_h1, ts)
        df_h4_s = slice_until_pandas(df_h4, ts)
        if len(df_m15_s) < 50 or len(df_h1_s) < 20 or len(df_h4_s) < 5:
            continue
        row = {}
        try:
            df_struct = structure_mod.build_structure_features(
                timestamps=[ts_str],
                candles_by_tf={"M15": candles_m15, "H1": candles_h1,
                               "H4": candles_h4, "D1": candles_d1},
            )
            for k, v in df_struct.iloc[0].items():
                key = f"structure__{k}"
                row[key] = float(v) if v == v else float("nan")
                feature_to_family[key] = "structure"
        except Exception as e:
            warnings.warn(str(e))

        try:
            df_vol = volatility_mod.compute_all_features(
                df_m15=df_m15_s, df_h1=df_h1_s, df_h4=df_h4_s,
            )
            for k in df_vol.columns:
                v = df_vol.iloc[-1][k]
                key = f"volatility__{k}"
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "volatility"
        except Exception as e:
            warnings.warn(str(e))

        try:
            def _r(d): return d.reset_index() if d is not None else d
            df_micro = microstructure_mod.compute_microstructure_features(
                df_m15=_r(df_m15), df_m1=_r(df_m1),
                df_h1=_r(df_h1), df_h4=_r(df_h4),
                ts_close=ts, symbol=TEST_INSTRUMENT, tick_df=None,
            )
            for k in df_micro.columns:
                v = df_micro.iloc[0][k]
                key = f"microstructure__{k}"
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "microstructure"
        except Exception as e:
            warnings.warn(str(e))

        try:
            ts_dict = time_session_mod.compute_time_session_features(
                ts=ts, symbol=TEST_INSTRUMENT,
            )
            for k, v in ts_dict.items():
                key = f"time_session__{k}"
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "time_session"
        except Exception as e:
            warnings.warn(str(e))

        try:
            liq_dict = liquidity_mod.extract_liquidity_features(
                candles_by_tf={"M15": candles_m15, "H1": candles_h1, "H4": candles_h4},
                anchor_idx_by_tf={"M15": anchor_by_tf["M15"], "H1": anchor_by_tf["H1"], "H4": anchor_by_tf["H4"]},
                instrument=TEST_INSTRUMENT, side="LONG", current_price=ref_price,
            )
            for k, v in liq_dict.items():
                key = f"liquidity__{k}"
                row[key] = float(v) if (v == v) else float("nan")
                feature_to_family[key] = "liquidity"
        except Exception as e:
            warnings.warn(str(e))

        try:
            regime_od = regime_mod.compute_regime_features(
                symbol=TEST_INSTRUMENT, ts=ts, side="LONG", ctx=regime_ctx,
            )
            for k, v in dict(regime_od).items():
                key = f"regime__{k}"
                try:
                    row[key] = float(v) if (v == v) else float("nan")
                except (TypeError, ValueError):
                    row[key] = float("nan")
                feature_to_family[key] = "regime"
        except Exception as e:
            warnings.warn(str(e))

        rows_out.append(row)

    df = pd.DataFrame(rows_out)
    df = df.loc[:, df.isna().mean() < 0.5]
    df = df.loc[:, df.var(axis=0) > 1e-12]
    print(f"after filter: {df.shape}")

    # Mark binary / low-cardinality columns. Heuristic: <=3 unique values OR
    # all values in {0.0, 1.0, NaN}.
    binary_cols = set()
    for c in df.columns:
        unique = df[c].dropna().unique()
        if len(unique) <= 3:
            binary_cols.add(c)
            continue
        # Check if all values are 0/1
        if set(unique).issubset({0.0, 1.0, -1.0}):
            binary_cols.add(c)
    print(f"binary/low-card cols: {len(binary_cols)} / {df.shape[1]}")
    continuous_cols = [c for c in df.columns if c not in binary_cols]
    df_cont = df[continuous_cols]
    print(f"continuous cols: {df_cont.shape[1]}")

    # Compute Spearman + Pearson on continuous-only
    print("computing Spearman (continuous)...")
    spearman = df_cont.corr(method="spearman")
    pearson = df_cont.corr(method="pearson")

    # Pairs
    cols = list(df_cont.columns)
    pairs = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            ci, cj = cols[i], cols[j]
            fam_i = feature_to_family.get(ci, "?")
            fam_j = feature_to_family.get(cj, "?")
            cross = fam_i != fam_j
            sp = spearman.iloc[i, j]
            pe = pearson.iloc[i, j]
            if pd.isna(sp) and pd.isna(pe):
                continue
            absmax = max(
                abs(sp) if not pd.isna(sp) else 0.0,
                abs(pe) if not pd.isna(pe) else 0.0,
            )
            pairs.append((absmax, ci, cj, fam_i, fam_j, cross, sp, pe))
    pairs.sort(reverse=True, key=lambda x: x[0])

    n_07 = sum(1 for p in pairs if p[0] >= 0.7)
    n_09 = sum(1 for p in pairs if p[0] >= 0.9)
    n_07_cross = sum(1 for p in pairs if p[5] and p[0] >= 0.7)
    n_09_cross = sum(1 for p in pairs if p[5] and p[0] >= 0.9)

    # Features touched by any |rho|>=0.7 partner
    touched = set()
    for p in pairs:
        if p[0] >= 0.7:
            touched.add(p[1])
            touched.add(p[2])

    top_cross = []
    for p in pairs:
        if p[5]:
            top_cross.append({
                "feature_a": p[1].split("__", 1)[1] if "__" in p[1] else p[1],
                "feature_b": p[2].split("__", 1)[1] if "__" in p[2] else p[2],
                "family_a": p[3], "family_b": p[4],
                "spearman_rho": float(p[6]) if not pd.isna(p[6]) else None,
                "pearson_rho": float(p[7]) if not pd.isna(p[7]) else None,
                "abs_max_rho": float(p[0]),
            })
            if len(top_cross) >= 20:
                break

    # Persist robust pairs CSV
    rob_csv = AUDIT / "q2_robust_top_corr_pairs.csv"
    with rob_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family_a", "feature_a", "family_b", "feature_b", "cross_family",
                    "spearman_rho", "pearson_rho", "abs_max_rho"])
        for p in pairs[:300]:
            w.writerow([
                p[3], p[1].split("__", 1)[1] if "__" in p[1] else p[1],
                p[4], p[2].split("__", 1)[1] if "__" in p[2] else p[2],
                p[5],
                f"{p[6]:.4f}" if not pd.isna(p[6]) else "",
                f"{p[7]:.4f}" if not pd.isna(p[7]) else "",
                f"{p[0]:.4f}",
            ])

    # Append to summary
    summary_path = AUDIT / "q2_correlation_summary.json"
    with summary_path.open(encoding="utf-8") as fh:
        existing = json.load(fh)
    existing["robust_recompute_continuous_only"] = {
        "cohort_size": int(df.shape[0]),
        "binary_or_low_cardinality_dropped": len(binary_cols),
        "continuous_columns_kept": int(df_cont.shape[1]),
        "all_pairs_above_0.7_abs": n_07,
        "all_pairs_above_0.9_abs": n_09,
        "cross_family_pairs_above_0.7_abs": n_07_cross,
        "cross_family_pairs_above_0.9_abs": n_09_cross,
        "features_with_at_least_one_high_corr_partner": len(touched),
        "top_20_cross_family_pairs": top_cross,
        "interpretation": (
            "Robust subset: continuous features only (binary/low-cardinality dropped). "
            "Removes spurious |rho|=1.0 from cohort hour-imbalance (most XAUUSD trades "
            "fall at hour 8 or 14 -> binary OH features get perfect correlation with "
            "anything constant within hour). Use these numbers as the redundancy gate "
            "magnitude estimate."
        ),
    }
    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(existing, fh, indent=2, default=str)
    print(f"continuous-only |rho|>=0.7 cross-family: {n_07_cross}")
    print(f"continuous-only |rho|>=0.9 cross-family: {n_09_cross}")
    print(f"continuous-only |rho|>=0.7 ALL pairs (cross + within-family): {n_07}")
    print(f"continuous-only |rho|>=0.9 ALL pairs: {n_09}")
    print("done.")


if __name__ == "__main__":
    main()
