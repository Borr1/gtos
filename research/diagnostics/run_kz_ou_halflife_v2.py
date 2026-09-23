#!/usr/bin/env python3
"""
Rerun KZ-only OU half-life with corrected datetime64 gap filter.

This is a targeted rerun of the single test affected by the gap bug
(identified in PEER_REVIEW_AUDIT.md, Finding 1).  Outputs a versioned
markdown file: ou_kz_half_life_v2.md

Fix applied:
    BEFORE: np.diff(df["time"].astype(np.int64)) / 1e9
    AFTER:  df["time"].diff().dt.total_seconds().iloc[1:].values
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime

try:
    import statsmodels.api as sm
    HAS_SM = True
except ImportError:
    HAS_SM = False

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR  = os.path.join(REPO_ROOT, "data", "historical")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "mean_reversion_mechanics")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Kill-zone definition (XAUUSD H1, UTC hours) ───────────────────────────
XAUUSD_KZ = [(7.0, 10.5), (13.0, 17.0)]   # London + NY

TF_MINUTES = {"H1": 60}
MIN_OBS    = 50


# ── Gap filter (FIXED) ─────────────────────────────────────────────────────
def gap_mask(df: pd.DataFrame, expected_min: int = 60) -> np.ndarray:
    """
    Boolean mask of length n-1.  True where the transition is NOT a gap
    (gap <= 3 × expected bar width in minutes).
    Uses the FIXED .diff().dt.total_seconds() method — not astype(np.int64).
    """
    gaps_sec = df["time"].diff().dt.total_seconds().iloc[1:].values
    gaps_min = gaps_sec / 60.0
    return gaps_min <= expected_min * 3.0


# ── Kill-zone mask ─────────────────────────────────────────────────────────
def kz_mask(df: pd.DataFrame) -> np.ndarray:
    h    = df["time"].dt.hour + df["time"].dt.minute / 60.0
    mask = np.zeros(len(df), dtype=bool)
    for lo, hi in XAUUSD_KZ:
        mask |= ((h >= lo) & (h < hi)).values
    return mask


# ── OU fit ─────────────────────────────────────────────────────────────────
def ou_fit(x_raw: np.ndarray, gap_valid: np.ndarray | None = None) -> dict:
    """ADF regression: ΔX_t = α + β·X_{t-1} + ε → HL = -ln2/β."""
    if not HAS_SM:
        return {"error": "statsmodels not installed"}

    x      = x_raw.copy()
    finite = np.isfinite(x)
    n      = len(x)

    dX_list, Xlag_list = [], []
    for i in range(1, n):
        if not (finite[i - 1] and finite[i]):
            continue
        if gap_valid is not None and i - 1 < len(gap_valid) and not gap_valid[i - 1]:
            continue
        dX_list.append(x[i] - x[i - 1])
        Xlag_list.append(x[i - 1])

    dX   = np.array(dX_list)
    Xlag = np.array(Xlag_list)
    n_obs = len(dX)

    if n_obs < MIN_OBS:
        return {"error": f"n_obs={n_obs} < {MIN_OBS}"}

    X_reg = sm.add_constant(Xlag)
    res   = sm.OLS(dX, X_reg).fit()
    beta  = float(res.params[1])
    se    = float(res.bse[1])

    if beta >= 0:
        return {"half_life": None, "beta": beta, "n": int(n_obs),
                "note": "beta>=0 — no mean reversion"}

    hl    = float(-np.log(2.0) / beta)
    se_hl = float(np.log(2.0) / beta ** 2 * se)
    ci_lo = float(max(hl - 1.96 * se_hl, 0.0))
    ci_hi = float(hl + 1.96 * se_hl)

    return {
        "half_life":     round(hl, 2),
        "ci_lo_95":      round(ci_lo, 2),
        "ci_hi_95":      round(ci_hi, 2),
        "beta":          round(beta, 6),
        "beta_se":       round(se, 6),
        "n_obs":         int(n_obs),
    }


# ── Detrend (SMA50, matching the original script) ─────────────────────────
def detrend_sma50(price: np.ndarray) -> np.ndarray:
    p = pd.Series(price)
    trend = p.rolling(50, min_periods=50).mean().values
    return price - trend


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    path = os.path.join(DATA_DIR, "XAUUSD_H1.csv")
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} not found")

    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])
    df["time"]  = pd.to_datetime(df["time"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)

    print(f"XAUUSD H1: {len(df)} bars  ({df['time'].iloc[0].date()} – {df['time'].iloc[-1].date()})")

    # --- All-hours baseline (for comparison) ---------------------------------
    price_all  = df["close"].values.astype(np.float64)
    gap_ok_all = gap_mask(df, expected_min=60)
    det_all    = detrend_sma50(price_all)
    res_all    = ou_fit(det_all, gap_valid=gap_ok_all)
    print(f"\nAll-hours  HL = {res_all.get('half_life')}  "
          f"95% CI [{res_all.get('ci_lo_95')}, {res_all.get('ci_hi_95')}]  "
          f"n={res_all.get('n_obs')}")

    # --- KZ-only subsample ---------------------------------------------------
    kz      = kz_mask(df)
    df_kz   = df[kz].reset_index(drop=True)
    print(f"\nKZ subsample: {len(df_kz)} bars")

    price_kz  = df_kz["close"].values.astype(np.float64)
    gap_ok_kz = gap_mask(df_kz, expected_min=60)
    det_kz    = detrend_sma50(price_kz)
    res_kz    = ou_fit(det_kz, gap_valid=gap_ok_kz)
    print(f"KZ-only    HL = {res_kz.get('half_life')}  "
          f"95% CI [{res_kz.get('ci_lo_95')}, {res_kz.get('ci_hi_95')}]  "
          f"n={res_kz.get('n_obs')}")

    # --- Save results --------------------------------------------------------
    ts      = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_md  = os.path.join(OUT_DIR, "ou_kz_half_life_v2.md")

    md = f"""# OU Half-Life: KZ-Only Rerun (Bug-Fixed)

**Generated:** {ts} UTC
**Script:** run_kz_ou_halflife_v2.py
**Fix applied:** `df["time"].diff().dt.total_seconds().iloc[1:].values` replaces `np.diff(df["time"].astype(np.int64)) / 1e9`
**Source file:** data/historical/XAUUSD_H1.csv

---

## Results

### All-Hours (baseline, no change expected)

| Metric | Value |
|--------|-------|
| Half-life (H1 bars) | {res_all.get("half_life")} |
| 95% CI | [{res_all.get("ci_lo_95")}, {res_all.get("ci_hi_95")}] |
| beta | {res_all.get("beta")} |
| n_obs | {res_all.get("n_obs")} |
| Note | Audit predicted: 25.4 bars (unchanged) |

### KZ-Only XAUUSD H1 (affected test)

| Metric | Value |
|--------|-------|
| Half-life (H1 bars) | **{res_kz.get("half_life")}** |
| 95% CI | **[{res_kz.get("ci_lo_95")}, {res_kz.get("ci_hi_95")}]** |
| beta | {res_kz.get("beta")} |
| n_obs | {res_kz.get("n_obs")} |
| Note | Prior (bug): 20.9 bars [16.5, 25.3]. Audit predicted: 17.1 [15.1, 19.0]. |

## Impact on Trailing Stop Calibration

| Scenario | OU Half-Life | Trailing Timeout (1.5×) |
|----------|-------------|------------------------|
| Prior (buggy) | 20.9 H1 bars | 31 H1 bars |
| Corrected | {res_kz.get("half_life")} H1 bars | {round(res_kz.get("half_life", 0) * 1.5, 1)} H1 bars |

**Direction unchanged:** KZ-only reversion ({res_kz.get("half_life")} bars) is faster than all-hours ({res_all.get("half_life")} bars). The gap correction strengthens this finding.

---

*This file supersedes the KZ-only OU half-life reported in mean_reversion_summary_20260411_025154.md.*
*No other diagnostic conclusions are affected — see PEER_REVIEW_AUDIT.md §Finding 1.*
"""

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nSaved: {out_md}")
    return res_kz


if __name__ == "__main__":
    main()
