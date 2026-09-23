"""Compute Spearman stability scores for structure features against
realized R on the K54 v1 train+val cohort (F11 mechanical, pre-2026-04).

Usage:
    python research/ml_program/scripts/features/_compute_structure_stability.py

Outputs (overwrite):
    research/ml_program/feature_catalogs/structure_stability.csv

This script is invoked once during catalog construction; not part of
the production code path. It is gitignored (see .gitignore for the
research/ml_program/feature_catalogs/ tree if needed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "research" / "ml_program" / "scripts" / "features"))

from structure import build_structure_features, _df_to_candles  # noqa: E402


F11_PATH = PROJECT_ROOT / "research" / "edge_decomposition" \
    / "F11_ob_zone_original_geometry" / "population.jsonl"
DATA_DIR = PROJECT_ROOT / "data" / "historical_2026"
OUT_CSV = PROJECT_ROOT / "research" / "ml_program" / "feature_catalogs" \
    / "structure_stability.csv"

CUTOFF_ISO = "2026-04-01T00:00:00+00:00"  # K54 v1 train+val end
DATA_HARD_CUTOFF = "2026-04-28T23:59:59+00:00"  # Q1.2 holdout begins after


def load_f11_train_val() -> list[dict]:
    """Load F11 records with realized_r != None and bos_time < cutoff."""
    out = []
    with F11_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ob_r = rec.get("ob_retest", {}) or {}
            if ob_r.get("realized_r") is None:
                continue
            bos = rec.get("bos", {}) or {}
            bt = bos.get("bos_time", "")
            if not bt or bt >= CUTOFF_ISO:
                continue
            out.append(rec)
    return out


def load_candles_by_symbol() -> dict[str, dict[str, list[dict]]]:
    """Load all 4 TFs for all 7 instruments, truncated to data cutoff."""
    out: dict[str, dict[str, list[dict]]] = {}
    symbols = ["XAUUSD", "USDJPY", "GBPUSD", "GBPJPY", "US30_cash",
               "NAS100", "XAGUSD"]
    cutoff_ts = pd.Timestamp(DATA_HARD_CUTOFF)
    for sym in symbols:
        out[sym] = {}
        for tf in ("M15", "H1", "H4", "D1"):
            csv = DATA_DIR / f"{sym}_{tf}.csv"
            if not csv.exists():
                out[sym][tf] = []
                continue
            df = pd.read_csv(csv, parse_dates=["time"])
            # Localise naive timestamps to UTC if needed.
            if df["time"].dt.tz is None:
                df["time"] = df["time"].dt.tz_localize("UTC")
            df = df[df["time"] <= cutoff_ts]
            out[sym][tf] = _df_to_candles(df)
    return out


def main() -> None:
    print("Loading F11 train+val cohort ...")
    recs = load_f11_train_val()
    print(f"  {len(recs)} F11 records (filled, pre-2026-04)")

    print("Loading OHLCV (4 TFs × 7 instruments) ...")
    candles = load_candles_by_symbol()

    print("Computing structure features per record ...")
    rows = []
    rs = []
    for i, rec in enumerate(recs):
        bos = rec["bos"]
        sym = bos["symbol"]
        ts = bos["bos_time"]
        # Strip tz for compatibility with structure._slice_candles_until,
        # which compares on string prefix.
        ts_clean = ts.replace("+00:00", "").replace("Z", "")
        cs = candles.get(sym, {})
        if not cs.get("M15"):
            continue
        feats = build_structure_features([ts_clean], cs)
        if feats.empty:
            continue
        rows.append(feats.iloc[0].to_dict())
        rs.append(float(rec["ob_retest"]["realized_r"]))
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(recs)} done")
    print(f"Computed {len(rows)} feature rows.")

    feat_df = pd.DataFrame(rows)
    rs_arr = pd.Series(rs, name="realized_r")

    # Spearman correlation per column
    print("Computing Spearman correlations ...")
    out_rows = []
    for col in feat_df.columns:
        s = feat_df[col]
        # Skip columns that are all-NaN or constant
        valid = s.notna() & rs_arr.notna()
        n_valid = int(valid.sum())
        if n_valid < 30:
            out_rows.append({"feature": col, "rho": np.nan, "n": n_valid, "p": np.nan})
            continue
        sv = s[valid]
        rv = rs_arr[valid]
        if sv.nunique() < 2:
            out_rows.append({"feature": col, "rho": np.nan, "n": n_valid, "p": np.nan})
            continue
        # Manual Spearman: rank both and compute Pearson on ranks.
        sr = sv.rank()
        rr = rv.rank()
        # Pearson formula
        sr_c = sr - sr.mean()
        rr_c = rr - rr.mean()
        denom = np.sqrt((sr_c ** 2).sum() * (rr_c ** 2).sum())
        if denom == 0:
            rho = np.nan
            p = np.nan
        else:
            rho = float((sr_c * rr_c).sum() / denom)
            # t-statistic for Spearman approx (large-n normal approx).
            try:
                t = rho * np.sqrt((n_valid - 2) / max(1e-12, 1 - rho * rho))
                # 2-sided p from normal approx (large-sample)
                from math import erfc
                p = float(erfc(abs(t) / np.sqrt(2)))
            except Exception:
                p = np.nan
        out_rows.append({"feature": col, "rho": rho, "n": n_valid, "p": p})

    out_df = pd.DataFrame(out_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV}: {len(out_df)} rows")
    # Quick top-15 by |rho|
    top = out_df.dropna(subset=["rho"]).copy()
    top["abs_rho"] = top["rho"].abs()
    top = top.sort_values("abs_rho", ascending=False).head(15)
    print("\nTop 15 features by |Spearman rho|:")
    print(top[["feature", "rho", "n", "p"]].to_string(index=False))


if __name__ == "__main__":
    main()
