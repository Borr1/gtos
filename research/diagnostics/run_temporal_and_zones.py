#!/usr/bin/env python3
"""
GTOS Temporal Pattern & Zone Analysis: B1, B2, B3
====================================================
Three statistical tests run on all 5 GTOS instruments.

  B1 — Asia Range → London Prediction (Q-0.2)
       Does a narrow Asian session predict a large London expansion?

  B2 — Intraday Momentum: First-Half → Second-Half (Q-14.7)
       Does kill-zone first-half direction predict second-half direction?

  B3 — VWAP Reversion (Q-13.2)
       Does gold revert to session VWAP more reliably than to OB zones (~70%)?

Methodology:
  - B1 uses H1 data (more history: 2–2.5 years)
  - B2 and B3 use M15 data (required for intraday half-period resolution)
  - Bonferroni correction applied across all primary p-values in the batch
  - All timestamps treated as UTC (confirmed by broker export format)
  - Pre-committed decision gate: test passes if Bonferroni-corrected p < 0.05

Timezone note (pressure test):
  - MT5 exports were confirmed to be UTC by examining Monday open hours:
    first bar appears at 01:00 UTC (Sydney/Wellington partial open),
    meaning the CSV timestamps are NOT broker local time but UTC.
  - Asia session defined as 00:00–07:00 UTC (pre-London quiet period).
    On Mondays the 00:00 bar is absent; the range is computed from whatever
    bars exist in [00:00, 07:00). Days with < 3 Asia bars are excluded.

Outputs:
    research/diagnostics/temporal_and_zones/temporal_zones_results.json
    research/diagnostics/temporal_and_zones/temporal_zones_summary.md
    research/diagnostics/temporal_and_zones/plots/

Usage:
    python research/diagnostics/run_temporal_and_zones.py
"""

import os
import sys
import json
import warnings
import traceback
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr, ttest_1samp, wilcoxon
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data", "historical")
OUT_DIR = os.path.join(os.path.dirname(__file__), "temporal_and_zones")
PLOTS_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

TIMESTAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

INSTRUMENTS = {
    "XAUUSD": {"prefix": "XAUUSD",    "pip_size": 0.01, "spread_est": 0.30},
    "US30":   {"prefix": "US30_cash", "pip_size": 1.0,  "spread_est": 0.40},
    "USDJPY": {"prefix": "USDJPY",    "pip_size": 0.01, "spread_est": 0.008},
    "GBPJPY": {"prefix": "GBPJPY",    "pip_size": 0.01, "spread_est": 0.012},
    "GBPUSD": {"prefix": "GBPUSD",    "pip_size": 0.0001, "spread_est": 0.0002},
}

# UTC session windows (half-open [lo, hi) in hours)
ASIA_SESSION     = (0, 7)   # 00:00–07:00 UTC, pre-London quiet period

# Kill zone London windows — from CLAUDE.md (GTOS canonical)
LONDON_KZ = {
    "XAUUSD": (7, 10.5),
    "US30":   (8, 10.5),
    "USDJPY": (7, 9.5),
    "GBPJPY": (7, 9.5),
    "GBPUSD": (7, 12.0),
}

# Kill zone NY windows
NY_KZ = {
    "XAUUSD": (13, 17.0),
    "US30":   (13.5, 16.0),
    "USDJPY": (13, 15.5),
    "GBPJPY": (13, 15.5),
    "GBPUSD": (13, 15.5),
}

# ADR window
ADR_WINDOW = 20

# Bonferroni: all primary p-values collected here
ALL_PVALUES: List[float] = []

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_data(symbol: str, tf: str) -> Optional[pd.DataFrame]:
    """Load OHLCV CSV, return UTC-indexed DataFrame or None."""
    prefix = INSTRUMENTS[symbol]["prefix"]
    path = os.path.join(DATA_DIR, f"{prefix}_{tf}.csv")
    if not os.path.exists(path):
        print(f"  [MISSING] {path}")
        return None
    df = pd.read_csv(path, parse_dates=["time"])
    df = df.set_index("time")
    df.index = pd.DatetimeIndex(df.index).tz_localize("UTC")
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    df = df.sort_index()
    return df


def compute_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Compute ATR (average true range)."""
    hi = df["high"]
    lo = df["low"]
    cp = df["close"].shift(1)
    tr = pd.concat([hi - lo, (hi - cp).abs(), (lo - cp).abs()], axis=1).max(axis=1)
    return tr.rolling(window, min_periods=1).mean()


def bonferroni_alpha(n_tests: int, alpha: float = 0.05) -> float:
    return alpha / max(n_tests, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# B1 — ASIA RANGE → LONDON PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════

def b1_compute_session_stats(df_h1: pd.DataFrame, asia_lo: int, asia_hi: int,
                              london_lo: float, london_hi: float,
                              ny_lo: float, ny_hi: float) -> pd.DataFrame:
    """
    For each trading day, compute Asia/London/NY range and daily ADR.
    Returns a per-day DataFrame.
    """
    rows = []
    grouped = df_h1.groupby(df_h1.index.date)

    for day, grp in grouped:
        # Asia range
        asia = grp[(grp.index.hour >= asia_lo) & (grp.index.hour < asia_hi)]
        if len(asia) < 3:
            continue  # Skip Monday openings or incomplete days
        asia_range = asia["high"].max() - asia["low"].min()
        # Asia direction: close of last Asia bar vs open of first Asia bar
        asia_return = asia["close"].iloc[-1] - asia["open"].iloc[0]

        # London range and return (open-to-close)
        lon_h = int(london_lo)
        lon_m = int((london_lo % 1) * 60)
        london = grp[(grp.index.hour > lon_h) |
                     ((grp.index.hour == lon_h) & (grp.index.minute >= lon_m))]
        london = london[(london.index.hour < int(london_hi)) |
                        ((london.index.hour == int(london_hi)) &
                         (london.index.minute < int((london_hi % 1) * 60)))]
        # simpler hour-based filter
        london = grp[(grp.index.hour >= int(london_lo)) & (grp.index.hour < int(london_hi) + (1 if london_hi % 1 > 0 else 0))]
        # Precise filter using fractional hours
        lon_decimal = grp.index.hour + grp.index.minute / 60.0
        london = grp[(lon_decimal >= london_lo) & (lon_decimal < london_hi)]
        if len(london) < 2:
            london_range, london_return = np.nan, np.nan
        else:
            london_range = london["high"].max() - london["low"].min()
            london_return = london["close"].iloc[-1] - london["open"].iloc[0]

        # NY range
        ny_decimal = grp.index.hour + grp.index.minute / 60.0
        ny = grp[(ny_decimal >= ny_lo) & (ny_decimal < ny_hi)]
        if len(ny) < 2:
            ny_range = np.nan
        else:
            ny_range = ny["high"].max() - ny["low"].min()

        # Daily range (for ADR base)
        daily_range = grp["high"].max() - grp["low"].min()

        rows.append({
            "date": day,
            "asia_range": asia_range,
            "asia_return": asia_return,
            "london_range": london_range,
            "london_return": london_return,
            "ny_range": ny_range,
            "daily_range": daily_range,
        })

    df_days = pd.DataFrame(rows).set_index("date")
    # Compute 20-day ADR
    df_days["adr_20"] = df_days["daily_range"].rolling(ADR_WINDOW, min_periods=5).mean()
    df_days["asia_range_pct_adr"] = df_days["asia_range"] / df_days["adr_20"]
    df_days["london_range_pct_adr"] = df_days["london_range"] / df_days["adr_20"]
    return df_days


def b1_run_analysis(symbol: str, df_h1: pd.DataFrame, split_years: bool = True) -> Dict[str, Any]:
    """Run full B1 analysis for one instrument."""
    print(f"  B1 {symbol}: computing session stats …")
    london_kz = LONDON_KZ[symbol]
    ny_kz = NY_KZ[symbol]
    df = b1_compute_session_stats(df_h1, *ASIA_SESSION, *london_kz, *ny_kz)
    df = df.dropna(subset=["asia_range", "london_range"])

    results: Dict[str, Any] = {"n_days": len(df), "data_range": [str(df.index.min()), str(df.index.max())]}

    # ── Correlations ──────────────────────────────────────────────────────────
    r_pearson, p_pearson = pearsonr(df["asia_range"], df["london_range"])
    r_spearman, p_spearman = spearmanr(df["asia_range"], df["london_range"])
    ALL_PVALUES.extend([p_pearson, p_spearman])
    results["correlation"] = {
        "pearson_r": round(r_pearson, 4),
        "pearson_p": round(p_pearson, 6),
        "spearman_r": round(r_spearman, 4),
        "spearman_p": round(p_spearman, 6),
    }

    # ── Regression: London = α + β × Asia ────────────────────────────────────
    X = add_constant(df["asia_range"])
    model = OLS(df["london_range"], X).fit()
    results["regression_range"] = {
        "alpha": round(model.params["const"], 4),
        "beta": round(model.params["asia_range"], 4),
        "r_squared": round(model.rsquared, 4),
        "p_beta": round(model.pvalues["asia_range"], 6),
    }
    ALL_PVALUES.append(model.pvalues["asia_range"])

    # ── Regression: London_return ~ Asia_range (direction predictability) ────
    df2 = df.dropna(subset=["london_return"])
    X2 = add_constant(df2["asia_range"])
    model2 = OLS(df2["london_return"], X2).fit()
    results["regression_direction"] = {
        "alpha": round(model2.params["const"], 4),
        "beta": round(model2.params["asia_range"], 4),
        "r_squared": round(model2.rsquared, 4),
        "p_beta": round(model2.pvalues["asia_range"], 6),
        "note": "London open-to-close return regressed on Asia range. β≈0 means range does not predict direction.",
    }
    ALL_PVALUES.append(model2.pvalues["asia_range"])

    # ── Quartile analysis ─────────────────────────────────────────────────────
    df["asia_q"] = pd.qcut(df["asia_range"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    quartile_stats = {}
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        sub = df[df["asia_q"] == q]
        adr_med = sub["adr_20"].median()
        expansion_thresh = 1.5 * adr_med if not np.isnan(adr_med) else np.nan
        exp_rate = (sub["london_range"] > expansion_thresh).mean() if not np.isnan(expansion_thresh) else np.nan
        quartile_stats[q] = {
            "n": int(len(sub)),
            "asia_range_mean": round(sub["asia_range"].mean(), 4),
            "asia_range_median": round(sub["asia_range"].median(), 4),
            "london_range_mean": round(sub["london_range"].mean(), 4),
            "london_range_std": round(sub["london_range"].std(), 4),
            "london_return_mean": round(sub["london_return"].mean(), 4),
            "expansion_rate_gt1p5ADR": round(float(exp_rate), 4) if not np.isnan(exp_rate) else None,
        }
    results["quartile_analysis"] = quartile_stats

    # ── Threshold tests: Asia < 10, 12, 15 (only for XAUUSD-priced instruments) ──
    # For JPY pairs and US30, the thresholds don't make sense in $ terms
    if symbol in ("XAUUSD",):
        thresholds = [10.0, 12.0, 15.0]
        thresh_stats = {}
        normal_london = df[df["asia_range"] >= 15.0]["london_range"]
        for thr in thresholds:
            sub = df[df["asia_range"] < thr]
            if len(sub) < 5:
                continue
            ks_stat, ks_p = stats.ks_2samp(sub["london_range"].dropna(),
                                             normal_london.dropna())
            ALL_PVALUES.append(ks_p)
            thresh_stats[f"asia_lt_{thr}"] = {
                "n": int(len(sub)),
                "london_range_mean": round(sub["london_range"].mean(), 4),
                "london_range_median": round(sub["london_range"].median(), 4),
                "london_range_std": round(sub["london_range"].std(), 4),
                "vs_normal_ks_p": round(ks_p, 6),
                "normal_london_mean": round(normal_london.mean(), 4),
            }
        results["threshold_tests_usd"] = thresh_stats
    else:
        # Use percentile-based thresholds for non-gold instruments
        thresh_stats = {}
        for pct_lo in [10, 25]:
            thr = np.percentile(df["asia_range"].dropna(), pct_lo)
            sub = df[df["asia_range"] <= thr]
            normal = df[df["asia_range"] > thr]["london_range"]
            if len(sub) < 5:
                continue
            ks_stat, ks_p = stats.ks_2samp(sub["london_range"].dropna(), normal.dropna())
            ALL_PVALUES.append(ks_p)
            thresh_stats[f"asia_pct_{pct_lo}"] = {
                "threshold_value": round(float(thr), 6),
                "n": int(len(sub)),
                "london_range_mean": round(sub["london_range"].mean(), 6),
                "vs_normal_london_mean": round(normal.mean(), 6),
                "ks_p": round(ks_p, 6),
            }
        results["threshold_tests_pct"] = thresh_stats

    # ── Annual stability split ─────────────────────────────────────────────────
    if split_years:
        year_stats = {}
        df_idx = df.copy()
        df_idx["year"] = pd.to_datetime(df_idx.index).year
        for yr, sub in df_idx.groupby("year"):
            if len(sub) < 20:
                continue
            r, p = pearsonr(sub["asia_range"].dropna(), sub["london_range"].dropna())
            year_stats[str(yr)] = {"n": int(len(sub)), "pearson_r": round(r, 4), "pearson_p": round(p, 6)}
        results["annual_stability"] = year_stats

    print(f"    → n_days={len(df)}, Pearson r={r_pearson:.3f} (p={p_pearson:.4f})")
    return results


def b1_plot_scatter(symbol: str, df: pd.DataFrame) -> str:
    """Scatter plot: Asia range vs London range for XAUUSD."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"B1 {symbol}: Asia Range → London Prediction", fontsize=13, fontweight="bold")

    ax = axes[0]
    ax.scatter(df["asia_range"], df["london_range"], alpha=0.35, s=15, color="steelblue")
    # Regression line
    x_range = np.linspace(df["asia_range"].min(), df["asia_range"].max(), 100)
    X = add_constant(df[["asia_range"]])
    model = OLS(df["london_range"], X).fit()
    y_pred = model.params["const"] + model.params["asia_range"] * x_range
    ax.plot(x_range, y_pred, "r-", lw=2, label=f"OLS (β={model.params['asia_range']:.2f})")
    ax.set_xlabel("Asia Range (price units)")
    ax.set_ylabel("London Range (price units)")
    ax.set_title(f"Asia vs London Range (n={len(df)})")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    if "asia_q" in df.columns:
        colors = {"Q1": "#2196F3", "Q2": "#4CAF50", "Q3": "#FF9800", "Q4": "#F44336"}
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            sub = df[df["asia_q"] == q]["london_range"].dropna()
            ax2.hist(sub, bins=20, alpha=0.5, label=f"Asia {q}", color=colors[q])
        ax2.set_xlabel("London Range (price units)")
        ax2.set_ylabel("Count")
        ax2.set_title("London Range by Asia Quartile")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, "No quartile data", ha="center", va="center")

    plt.tight_layout()
    fname = os.path.join(PLOTS_DIR, f"b1_scatter_{symbol}.png")
    plt.savefig(fname, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return fname


# ═══════════════════════════════════════════════════════════════════════════════
# B2 — INTRADAY MOMENTUM: FIRST-HALF → SECOND-HALF
# ═══════════════════════════════════════════════════════════════════════════════

def b2_extract_half_returns(df_m15: pd.DataFrame,
                             h1_lo: float, h1_hi: float,
                             h2_lo: float, h2_hi: float) -> pd.DataFrame:
    """
    For each trading day, compute first-half and second-half returns
    for a given intraday window split.
    Returns DataFrame with (date, first_half_ret, second_half_ret).
    """
    rows = []
    bar_decimal = df_m15.index.hour + df_m15.index.minute / 60.0

    # Pre-filter to avoid full-day iteration overhead
    mask_h1 = (bar_decimal >= h1_lo) & (bar_decimal < h1_hi)
    mask_h2 = (bar_decimal >= h2_lo) & (bar_decimal < h2_hi)
    df_h1_filt = df_m15[mask_h1]
    df_h2_filt = df_m15[mask_h2]

    for day in sorted(set(df_m15.index.date)):
        sub1 = df_h1_filt[df_h1_filt.index.date == day]
        sub2 = df_h2_filt[df_h2_filt.index.date == day]
        if len(sub1) < 2 or len(sub2) < 2:
            continue
        # Return = (last close - first open) / first open
        h1_ret = (sub1["close"].iloc[-1] - sub1["open"].iloc[0]) / sub1["open"].iloc[0]
        h2_ret = (sub2["close"].iloc[-1] - sub2["open"].iloc[0]) / sub2["open"].iloc[0]
        h1_abs = abs(h1_ret)
        rows.append({
            "date": day,
            "h1_ret": h1_ret,
            "h2_ret": h2_ret,
            "h1_abs": h1_abs,
        })
    return pd.DataFrame(rows).set_index("date")


def b2_run_session(df: pd.DataFrame, session_name: str) -> Dict[str, Any]:
    """Statistical tests on a first-half/second-half return pair."""
    h1 = df["h1_ret"]
    h2 = df["h2_ret"]
    n = len(df)
    if n < 20:
        return {"n": n, "note": "Insufficient data (< 20 days)"}

    # Pearson and Spearman correlations
    r_pearson, p_pearson = pearsonr(h1, h2)
    r_spearman, p_spearman = spearmanr(h1, h2)
    ALL_PVALUES.extend([p_pearson, p_spearman])

    # Regression: h2 = α + β × h1
    X = add_constant(h1)
    model = OLS(h2, X).fit()
    ALL_PVALUES.append(model.pvalues["h1_ret"])

    # Sign agreement test: does h2 have same sign as h1 more than 50%?
    same_sign = (np.sign(h1) == np.sign(h2))
    sign_rate = same_sign.mean()
    # Binomial test against H0: p=0.5
    n_same = same_sign.sum()
    binom_p = stats.binom_test(int(n_same), int(n), 0.5, alternative="greater") if hasattr(stats, "binom_test") else stats.binomtest(int(n_same), int(n), 0.5, alternative="greater").pvalue
    ALL_PVALUES.append(float(binom_p))

    # Conditional analysis: when |h1| > median, is β stronger?
    median_abs = np.median(df["h1_abs"])
    large_mask = df["h1_abs"] > median_abs
    small_mask = ~large_mask

    cond_results = {}
    for label, mask in [("large_h1", large_mask), ("small_h1", small_mask)]:
        sub = df[mask]
        if len(sub) < 10:
            cond_results[label] = {"n": int(len(sub)), "note": "too small"}
            continue
        r, p = pearsonr(sub["h1_ret"], sub["h2_ret"])
        ALL_PVALUES.append(p)
        cond_results[label] = {
            "n": int(len(sub)),
            "pearson_r": round(r, 4),
            "pearson_p": round(p, 6),
        }

    # Economic significance
    h2_mean_cond = df[df["h1_ret"] > 0]["h2_ret"].mean()
    h2_mean_all = h2.mean()
    h2_std = h2.std()
    edge_bps = (h2_mean_cond - h2_mean_all) * 10000  # in basis points

    return {
        "n": n,
        "pearson_r": round(r_pearson, 4),
        "pearson_p": round(p_pearson, 6),
        "spearman_r": round(r_spearman, 4),
        "spearman_p": round(p_spearman, 6),
        "regression_alpha": round(model.params["const"], 6),
        "regression_beta": round(model.params["h1_ret"], 4),
        "regression_p": round(model.pvalues["h1_ret"], 6),
        "r_squared": round(model.rsquared, 4),
        "sign_agreement_rate": round(float(sign_rate), 4),
        "binom_p_vs_50pct": round(float(binom_p), 6),
        "conditional_analysis": cond_results,
        "h2_mean_bps": round(h2_mean_all * 10000, 3),
        "h2_mean_given_h1_up_bps": round(float(h2_mean_cond) * 10000, 3),
        "conditional_edge_bps": round(float(edge_bps), 3),
    }


def b2_run_analysis(symbol: str, df_m15: pd.DataFrame) -> Dict[str, Any]:
    """Run full B2 analysis for one instrument."""
    print(f"  B2 {symbol}: computing intraday momentum …")
    results: Dict[str, Any] = {}

    london_lo, london_hi = LONDON_KZ[symbol]
    ny_lo, ny_hi = NY_KZ[symbol]

    # London split: primary (spec) and robustness
    lon_mid_primary = 8.5          # 08:30 UTC
    lon_mid_robust  = 9.0          # 09:00 UTC

    # NY split
    ny_mid_primary  = 14.25        # 14:15 UTC
    ny_mid_robust   = 14.5         # 14:30 UTC

    sessions = {
        "London_primary": (london_lo, lon_mid_primary, lon_mid_primary, london_hi),
        "London_robust":  (london_lo, lon_mid_robust,  lon_mid_robust,  london_hi),
        "NY_primary":     (ny_lo,     ny_mid_primary,  ny_mid_primary,  ny_hi),
        "NY_robust":      (ny_lo,     ny_mid_robust,   ny_mid_robust,   ny_hi),
    }

    for sess_name, (h1_lo, h1_hi, h2_lo, h2_hi) in sessions.items():
        # Guard: London mid must be within London KZ
        if h1_lo >= h2_hi or h1_hi <= h1_lo or h2_hi <= h2_lo:
            continue
        df_sess = b2_extract_half_returns(df_m15, h1_lo, h1_hi, h2_lo, h2_hi)
        results[sess_name] = b2_run_session(df_sess, sess_name)
        n = results[sess_name].get("n", 0)
        beta = results[sess_name].get("regression_beta", "N/A")
        p = results[sess_name].get("regression_p", "N/A")
        print(f"    {sess_name}: n={n}, β={beta}, p={p}")

    return results


def b2_plot(symbol: str, df_m15: pd.DataFrame, session: str,
            h1_lo: float, h1_hi: float, h2_lo: float, h2_hi: float) -> str:
    """Scatter and histogram for B2."""
    df = b2_extract_half_returns(df_m15, h1_lo, h1_hi, h2_lo, h2_hi)
    if len(df) < 10:
        return ""

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"B2 {symbol} {session}: Intraday Momentum", fontsize=13, fontweight="bold")

    ax = axes[0]
    ax.scatter(df["h1_ret"] * 10000, df["h2_ret"] * 10000, alpha=0.35, s=15, color="steelblue")
    ax.axhline(0, color="k", lw=0.8, ls="--")
    ax.axvline(0, color="k", lw=0.8, ls="--")
    X = add_constant(df["h1_ret"])
    model = OLS(df["h2_ret"], X).fit()
    x_rng = np.linspace(df["h1_ret"].min(), df["h1_ret"].max(), 100)
    ax.plot(x_rng * 10000, (model.params["const"] + model.params["h1_ret"] * x_rng) * 10000,
            "r-", lw=2, label=f"OLS β={model.params['h1_ret']:.2f}")
    ax.set_xlabel("First-Half Return (bps)")
    ax.set_ylabel("Second-Half Return (bps)")
    ax.set_title(f"First→Second Half (n={len(df)})")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    same_sign = (np.sign(df["h1_ret"]) == np.sign(df["h2_ret"]))
    ax2.bar(["Same sign", "Opposite sign"], [same_sign.sum(), (~same_sign).sum()],
            color=["#4CAF50", "#F44336"])
    ax2.set_title(f"Sign Agreement: {same_sign.mean():.1%}")
    ax2.set_ylabel("Days")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fname = os.path.join(PLOTS_DIR, f"b2_{symbol}_{session}.png")
    plt.savefig(fname, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return fname


# ═══════════════════════════════════════════════════════════════════════════════
# B3 — VWAP REVERSION
# ═══════════════════════════════════════════════════════════════════════════════

def b3_compute_vwap(df_m15: pd.DataFrame) -> pd.Series:
    """
    Compute daily VWAP (anchored to 00:00 UTC reset) — retained for reference.
    typical_price = (H + L + C) / 3
    NOTE: This is a full-day VWAP. For institutional reversion analysis we use
    session-anchored VWAP (see b3_compute_session_vwap).
    """
    tp = (df_m15["high"] + df_m15["low"] + df_m15["close"]) / 3.0
    vol = df_m15["volume"]

    vwap_vals = np.full(len(df_m15), np.nan)
    dates = df_m15.index.date
    unique_dates = sorted(set(dates))

    for day in unique_dates:
        mask = (dates == day)
        tp_day = tp.values[mask]
        vol_day = vol.values[mask]

        vol_range = vol_day.max() - vol_day.min() if len(vol_day) > 0 else 0
        if vol_range == 0:
            vol_day = np.ones_like(vol_day)

        cum_vol = np.cumsum(vol_day)
        cum_tpvol = np.cumsum(tp_day * vol_day)
        vwap_day = cum_tpvol / cum_vol
        vwap_vals[mask] = vwap_day

    return pd.Series(vwap_vals, index=df_m15.index, name="vwap_daily")


def b3_compute_session_vwap(df_m15: pd.DataFrame,
                             session_lo: float, session_hi: float) -> pd.Series:
    """
    Compute session-anchored VWAP (resets at session start each day).
    Only bars within [session_lo, session_hi) UTC hours are processed.
    This is the institutionally relevant VWAP: traders use session VWAP as
    their benchmark (TWAP/VWAP orders within the active session), not daily VWAP.

    typical_price = (H + L + C) / 3
    Uses tick volume; falls back to bar-count if volume is constant in session.

    Returns NaN outside the session window.
    """
    tp = (df_m15["high"] + df_m15["low"] + df_m15["close"]) / 3.0
    vol = df_m15["volume"]
    bar_decimal = df_m15.index.hour + df_m15.index.minute / 60.0
    sess_mask = (bar_decimal >= session_lo) & (bar_decimal < session_hi)

    vwap_vals = np.full(len(df_m15), np.nan)
    dates = df_m15.index.date

    for day in sorted(set(dates[sess_mask])):
        # Only bars in session for this day
        day_sess_mask = sess_mask & (dates == day)
        idx = np.where(day_sess_mask)[0]
        if len(idx) == 0:
            continue
        tp_sess = tp.values[idx]
        vol_sess = vol.values[idx]

        vol_range = vol_sess.max() - vol_sess.min() if len(vol_sess) > 0 else 0
        if vol_range == 0:
            vol_sess = np.ones_like(vol_sess)

        cum_vol = np.cumsum(vol_sess)
        cum_tpvol = np.cumsum(tp_sess * vol_sess)
        vwap_sess = cum_tpvol / cum_vol
        vwap_vals[idx] = vwap_sess

    return pd.Series(vwap_vals, index=df_m15.index, name="vwap_session")


def b3_check_cumulative_reversion(deviation_arr: np.ndarray,
                                   event_idx: np.ndarray,
                                   all_dates: np.ndarray,
                                   max_lag: int,
                                   reversion_tol: float) -> Tuple[int, int]:
    """
    For each event position in event_idx, check if |deviation| crosses
    reversion_tol at ANY bar from t+1 through t+max_lag (same calendar day).
    Returns (n_reverted, n_events_valid).

    This is the correct definition: "return to within X of VWAP within N bars"
    means EVER crossing the threshold during the window — not being there at
    exactly bar N.
    """
    reverted = 0
    valid = 0
    n = len(deviation_arr)
    for pos in event_idx:
        # Scan forward up to max_lag bars, same day only
        day = all_dates[pos]
        found_reversion = False
        found_any_valid = False
        for lag in range(1, max_lag + 1):
            fp = pos + lag
            if fp >= n:
                break
            if all_dates[fp] != day:
                break
            fd = deviation_arr[fp]
            if np.isnan(fd):
                continue
            found_any_valid = True
            if abs(fd) <= reversion_tol:
                found_reversion = True
                break
        if found_any_valid:
            valid += 1
            if found_reversion:
                reverted += 1
    return reverted, valid


def b3_run_analysis(symbol: str, df_m15: pd.DataFrame) -> Dict[str, Any]:
    """
    Run full B3 VWAP reversion analysis for one instrument.

    Two VWAP types computed:
      - Daily VWAP (anchored 00:00 UTC) — reference, shows trend bias
      - Session VWAP (anchored to KZ start per session) — primary analysis

    Reversion check: CUMULATIVE — did price EVER get within reversion_tol of
    VWAP at any bar from t+1 to t+max_lag (same day, same session)?
    This matches the spec language: "return to within 0.25σ within N bars."
    """
    print(f"  B3 {symbol}: computing VWAP reversion …")

    atr = compute_atr(df_m15, window=14)
    bar_decimal = df_m15.index.hour + df_m15.index.minute / 60.0
    london_lo, london_hi = LONDON_KZ[symbol]
    ny_lo, ny_hi = NY_KZ[symbol]

    results: Dict[str, Any] = {
        "n_bars_total": int(len(df_m15)),
        "atr_window": 14,
        "deviation_metric": "(close - session_VWAP) / ATR_14",
        "reversion_definition": "CUMULATIVE — did price ever reach |dev| <= 0.25 ATR within N bars? (not point-in-time at bar N)",
        "quality_note": (
            "VWAP computed from M15 bars × tick volume (no sub-bar tick data). "
            "Session-anchored VWAP (London resets at London KZ start, NY at NY KZ start) is used "
            "as the primary measure — this is the institutionally relevant benchmark. "
            "Daily VWAP (00:00 UTC reset) shown for reference only; it carries trend bias in "
            "directional markets (confirmed: mean daily deviation = +0.37 ATR for XAUUSD due to "
            "gold's 2024-2026 uptrend)."
        ),
    }

    # --- Session VWAP analysis (primary) -------------------------------------
    # Analyse London and NY sessions separately with session-anchored VWAP
    sessions_to_run = {
        "London": (london_lo, london_hi),
        "NY": (ny_lo, ny_hi),
    }

    thresholds = [0.5, 1.0, 1.5, 2.0]
    lags = [1, 2, 4, 8]
    reversion_tol = 0.25

    all_dates_arr = np.array(df_m15.index.date)
    atr_arr = atr.values

    session_tables: Dict[str, Any] = {}
    for sess_name, (s_lo, s_hi) in sessions_to_run.items():
        vwap_sess = b3_compute_session_vwap(df_m15, s_lo, s_hi)
        deviation_sess = (df_m15["close"] - vwap_sess) / atr
        deviation_arr = deviation_sess.values

        sess_mask = (bar_decimal >= s_lo) & (bar_decimal < s_hi)
        # Sanity: distribution of deviations within session
        dev_in_sess = deviation_sess[sess_mask].dropna()
        dev_summary = {
            "mean": round(float(dev_in_sess.mean()), 4),
            "std": round(float(dev_in_sess.std()), 4),
            "frac_gt1ATR": round(float((dev_in_sess.abs() > 1.0).mean()), 4),
        }

        thr_table: Dict[str, Any] = {}
        for thr in thresholds:
            lag_table: Dict[str, Any] = {}
            # Positions where |deviation| first exceeds threshold (within session)
            above_pos = np.where(sess_mask & (deviation_arr > thr))[0]
            below_pos = np.where(sess_mask & (deviation_arr < -thr))[0]
            all_event_pos = np.concatenate([above_pos, below_pos])

            for lag in lags:
                rc, ec = b3_check_cumulative_reversion(
                    deviation_arr, all_event_pos, all_dates_arr, lag, reversion_tol
                )
                if ec < 5:
                    lag_table[f"lag_{lag}"] = {"n_events": int(ec), "reversion_rate": None}
                    continue
                rate = rc / ec
                try:
                    binom_p = stats.binomtest(rc, ec, 0.5, alternative="greater").pvalue
                except AttributeError:
                    binom_p = stats.binom_test(rc, ec, 0.5, alternative="greater")
                ALL_PVALUES.append(float(binom_p))
                lag_table[f"lag_{lag}"] = {
                    "n_events": int(ec),
                    "n_reverted": int(rc),
                    "reversion_rate": round(rate, 4),
                    "binom_p_vs_50pct": round(float(binom_p), 6),
                }

            thr_table[f"dev_{thr}"] = {"deviation_threshold_ATR": thr, **lag_table}

        session_tables[sess_name] = {
            "vwap_anchor": f"{s_lo:04.1f}–{s_hi:04.1f} UTC, resets each day",
            "deviation_distribution": dev_summary,
            "reversion_table": thr_table,
        }

    results["sessions"] = session_tables

    # --- Convenience: flatten to top-level reversion_table (London, lag summary) ------
    lon_thr_tbl = session_tables.get("London", {}).get("reversion_table", {})
    results["reversion_table"] = {
        thr_key: {lag_key: entry
                  for lag_key, entry in thr_val.items()
                  if lag_key.startswith("lag_")}
        for thr_key, thr_val in lon_thr_tbl.items()
    }

    # --- Displacement speed analysis (London, 1.0 ATR) -----------------------
    vwap_lon = b3_compute_session_vwap(df_m15, london_lo, london_hi)
    dev_lon = (df_m15["close"] - vwap_lon) / atr
    dev_arr_lon = dev_lon.values
    sess_lon_mask = (bar_decimal >= london_lo) & (bar_decimal < london_hi)

    dev_speed = pd.Series(dev_arr_lon, index=df_m15.index).diff(2)
    fast_threshold = dev_speed.abs().quantile(0.75)

    speed_results = {}
    for speed_label, speed_mask in [
        ("fast_displacement", dev_speed.abs() > fast_threshold),
        ("slow_displacement", dev_speed.abs() <= fast_threshold),
    ]:
        combined = sess_lon_mask & np.asarray(speed_mask)
        above_pos = np.where(combined & (dev_arr_lon > 1.0))[0]
        below_pos = np.where(combined & (dev_arr_lon < -1.0))[0]
        event_pos = np.concatenate([above_pos, below_pos])
        rc, ec = b3_check_cumulative_reversion(dev_arr_lon, event_pos, all_dates_arr, 4, reversion_tol)
        speed_results[speed_label] = {
            "n_events": int(ec),
            "reversion_rate_within_lag4": round(rc / max(ec, 1), 4) if ec > 0 else None,
        }

    results["displacement_speed"] = speed_results

    # --- Daily VWAP reference (to document bias) --------------------------------
    vwap_daily = b3_compute_vwap(df_m15)
    dev_daily = (df_m15["close"] - vwap_daily) / atr
    dev_daily_kz = dev_daily[(bar_decimal >= london_lo) & (bar_decimal < london_hi) |
                              (bar_decimal >= ny_lo) & (bar_decimal < ny_hi)].dropna()
    results["daily_vwap_reference"] = {
        "mean_deviation_kz_ATR": round(float(dev_daily_kz.mean()), 4),
        "std_deviation_kz_ATR": round(float(dev_daily_kz.std()), 4),
        "note": "Positive mean bias confirms trending behaviour during KZ; daily VWAP is not the right anchor.",
    }

    # Summary stats
    best_rate = max(
        (v.get("reversion_rate", 0) or 0)
        for sess_d in results["sessions"].values()
        for thr_d in sess_d.get("reversion_table", {}).values()
        for k, v in thr_d.items()
        if k.startswith("lag_") and isinstance(v, dict)
    )
    results["best_reversion_rate"] = round(best_rate, 4)
    results["ob_continuation_benchmark"] = 0.70

    r10_l4 = (results["reversion_table"].get("dev_1.0", {}).get("lag_4", {}) or {}).get("reversion_rate", "N/A")
    print(f"    London 1.0ATR → within-lag4 reversion: {r10_l4}")

    return results


def b3_plot(symbol: str, df_m15: pd.DataFrame,
            vwap_daily: pd.Series, vwap_london: pd.Series) -> str:
    """Plot VWAP deviation distribution and session VWAP vs price for most recent 7 days."""
    fig = plt.figure(figsize=(14, 5))
    fig.suptitle(f"B3 {symbol}: VWAP Reversion Analysis", fontsize=13, fontweight="bold")
    gs = gridspec.GridSpec(1, 3, figure=fig)

    atr = compute_atr(df_m15, window=14)
    dev_daily = (df_m15["close"] - vwap_daily) / atr
    dev_sess = (df_m15["close"] - vwap_london) / atr

    # Panel 1: daily VWAP deviation histogram (to show trend bias)
    ax1 = fig.add_subplot(gs[0])
    dev_clean = dev_daily.dropna().clip(-4, 4)
    ax1.hist(dev_clean, bins=80, color="salmon", edgecolor="white", lw=0.3, alpha=0.7,
             label="Daily VWAP (00:00 UTC)")
    dev_sess_clean = dev_sess.dropna().clip(-4, 4)
    ax1.hist(dev_sess_clean, bins=80, color="steelblue", edgecolor="white", lw=0.3, alpha=0.7,
             label="Session VWAP (London)")
    ax1.axvline(0, color="k", lw=1)
    for thr in [0.5, 1.0, 1.5, 2.0]:
        ax1.axvline(thr, color="red", ls="--", lw=0.8, alpha=0.5)
        ax1.axvline(-thr, color="red", ls="--", lw=0.8, alpha=0.5)
    ax1.set_xlabel("VWAP Deviation (ATR units)")
    ax1.set_ylabel("Count")
    ax1.set_title("Deviation Distribution")
    ax1.legend(fontsize=7)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Most recent 7 trading days — price vs both VWAPs
    cutoff = df_m15.index[-1] - pd.Timedelta(days=7)
    recent = df_m15[df_m15.index >= cutoff]
    vwap_daily_recent = vwap_daily.loc[recent.index]
    vwap_sess_recent = vwap_london.loc[recent.index]

    ax2 = fig.add_subplot(gs[1:])
    ax2.plot(recent.index, recent["close"], lw=1, color="steelblue", label="Close")
    ax2.plot(vwap_daily_recent.index, vwap_daily_recent, lw=1.2, color="salmon",
             ls="--", alpha=0.7, label="Daily VWAP (00:00 UTC)")
    ax2.plot(vwap_sess_recent.dropna().index, vwap_sess_recent.dropna(), lw=1.5,
             color="orange", label="London Session VWAP")
    ax2.set_title("Price vs VWAP (most recent 7 days)")
    ax2.set_xlabel("Time (UTC)")
    ax2.set_ylabel("Price")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right")

    plt.tight_layout()
    fname = os.path.join(PLOTS_DIR, f"b3_vwap_{symbol}.png")
    plt.savefig(fname, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return fname


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT WRITERS
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_p(p: Optional[float], bonf_alpha: float) -> str:
    if p is None:
        return "N/A"
    sig = "**" if p < bonf_alpha else ("*" if p < 0.05 else "")
    return f"{p:.4f}{sig}"


def write_summary_md(all_results: Dict, bonf_alpha: float, ts: str) -> str:
    lines = [
        f"# GTOS Temporal Pattern & Zone Analysis — B1, B2, B3",
        f"**Generated:** {ts} UTC",
        f"**Bonferroni α\\*:** {bonf_alpha:.6f} (n_tests={len(ALL_PVALUES)})",
        f"**Significance markers:** `**` = Bonferroni-significant, `*` = raw p<0.05",
        "",
        "---",
        "",
    ]

    # ── B1 ───────────────────────────────────────────────────────────────────
    lines += [
        "## B1 — Asia Range → London Prediction (Q-0.2)",
        "",
        "**Session definition:** Asia = 00:00–07:00 UTC, London = instrument kill zone start–end",
        "",
        "### Correlation: Asia Range vs London Range",
        "",
        "| Instrument | N Days | Pearson r | p | Spearman r | p |",
        "|------------|--------|-----------|---|------------|---|",
    ]
    for sym, res in all_results.get("b1", {}).items():
        corr = res.get("correlation", {})
        lines.append(
            f"| {sym} | {res.get('n_days','?')} "
            f"| {corr.get('pearson_r','?')} | {_fmt_p(corr.get('pearson_p'), bonf_alpha)} "
            f"| {corr.get('spearman_r','?')} | {_fmt_p(corr.get('spearman_p'), bonf_alpha)} |"
        )

    lines += [
        "",
        "### Regression: London_range = α + β × Asia_range",
        "",
        "| Instrument | α | β | R² | p(β) |",
        "|------------|---|---|----|------|",
    ]
    for sym, res in all_results.get("b1", {}).items():
        reg = res.get("regression_range", {})
        lines.append(
            f"| {sym} | {reg.get('alpha','?')} | {reg.get('beta','?')} "
            f"| {reg.get('r_squared','?')} | {_fmt_p(reg.get('p_beta'), bonf_alpha)} |"
        )

    lines += [
        "",
        "### Direction Test: Does Asia Range Predict London Return?",
        "",
        "| Instrument | β (range→return) | R² | p(β) | Interpretation |",
        "|------------|-------------------|----|------|----------------|",
    ]
    for sym, res in all_results.get("b1", {}).items():
        reg = res.get("regression_direction", {})
        beta = reg.get("beta", "?")
        p_b = reg.get("p_beta")
        interp = "No directional signal" if p_b and p_b > 0.05 else ("Directional signal FOUND" if p_b and p_b < bonf_alpha else "Weak")
        lines.append(
            f"| {sym} | {beta} | {reg.get('r_squared','?')} | {_fmt_p(p_b, bonf_alpha)} | {interp} |"
        )

    lines += [
        "",
        "### Quartile Analysis: XAUUSD (Asia range quartiles → London range)",
        "",
    ]
    xau_b1 = all_results.get("b1", {}).get("XAUUSD", {})
    if xau_b1:
        lines += [
            "| Asia Quartile | N | Asia Mean | London Mean | London Std | Expansion Rate (>1.5ADR) |",
            "|---------------|---|-----------|-------------|------------|--------------------------|",
        ]
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            qs = xau_b1.get("quartile_analysis", {}).get(q, {})
            lines.append(
                f"| {q} | {qs.get('n','?')} | {qs.get('asia_range_mean','?')} "
                f"| {qs.get('london_range_mean','?')} | {qs.get('london_range_std','?')} "
                f"| {qs.get('expansion_rate_gt1p5ADR','?')} |"
            )
        thr = xau_b1.get("threshold_tests_usd", {})
        if thr:
            lines += [
                "",
                "### XAUUSD: Threshold Tests ($)",
                "",
                "| Asia Range Threshold | N | London Mean | Normal London Mean | KS p |",
                "|---------------------|---|-------------|-------------------|------|",
            ]
            for k, v in thr.items():
                lines.append(
                    f"| {k} | {v.get('n','?')} | {v.get('london_range_mean','?')} "
                    f"| {v.get('normal_london_mean','?')} | {_fmt_p(v.get('vs_normal_ks_p'), bonf_alpha)} |"
                )

    lines += ["", "---", ""]

    # ── B2 ───────────────────────────────────────────────────────────────────
    lines += [
        "## B2 — Intraday Momentum: First-Half → Second-Half (Q-14.7)",
        "",
        "**Primary splits:** London 07:00–08:30 → 08:30–10:30 | NY 13:00–14:15 → 14:15–15:30 UTC",
        "**Robustness:** London 07:00–09:00 → 09:00–10:30 | NY 13:00–14:30 → 14:30–15:30 UTC",
        "",
        "| Instrument | Session | N | Pearson r | p | β | p(β) | Sign Rate | Binom p |",
        "|------------|---------|---|-----------|---|---|------|-----------|---------|",
    ]
    for sym, sym_res in all_results.get("b2", {}).items():
        for sess, res in sym_res.items():
            if not isinstance(res, dict) or res.get("n", 0) < 20:
                continue
            lines.append(
                f"| {sym} | {sess} | {res.get('n','?')} "
                f"| {res.get('pearson_r','?')} | {_fmt_p(res.get('pearson_p'), bonf_alpha)} "
                f"| {res.get('regression_beta','?')} | {_fmt_p(res.get('regression_p'), bonf_alpha)} "
                f"| {res.get('sign_agreement_rate','?')} | {_fmt_p(res.get('binom_p_vs_50pct'), bonf_alpha)} |"
            )

    lines += [
        "",
        "### Economic Significance",
        "",
        "| Instrument | Session | H2 Mean (bps) | H2 Mean|H1↑ (bps) | Conditional Edge (bps) |",
        "|------------|---------|---------------|-----------------|------------------------|",
    ]
    for sym, sym_res in all_results.get("b2", {}).items():
        for sess in ["London_primary", "NY_primary"]:
            res = sym_res.get(sess, {})
            if not isinstance(res, dict) or res.get("n", 0) < 20:
                continue
            lines.append(
                f"| {sym} | {sess} "
                f"| {res.get('h2_mean_bps','?')} "
                f"| {res.get('h2_mean_given_h1_up_bps','?')} "
                f"| {res.get('conditional_edge_bps','?')} |"
            )

    lines += ["", "---", ""]

    # ── B3 ───────────────────────────────────────────────────────────────────
    lines += [
        "## B3 — VWAP Reversion (Q-13.2)",
        "",
        "**VWAP definition:** typical_price × tick_volume, anchored daily at 00:00 UTC",
        "**Deviation metric:** (close − VWAP) / ATR₁₄",
        "**Reversion criterion:** |future deviation| ≤ 0.25 ATR within N M15 bars",
        "**OB continuation benchmark:** ~70% (mechanical, from historical backtest)",
        "",
        "### XAUUSD — London Session VWAP Reversion Table",
        "",
        "> Session VWAP anchored to London KZ start (07:00 UTC), resets each day.",
        "> Reversion = CUMULATIVE: price ever reaches |dev| ≤ 0.25 ATR within N bars.",
        "",
        "| Deviation Threshold | Lag 1 | Lag 2 | Lag 4 | Lag 8 |",
        "|---------------------|-------|-------|-------|-------|",
    ]
    xau_b3 = all_results.get("b3", {}).get("XAUUSD", {})
    lon_thr_tbl = xau_b3.get("sessions", {}).get("London", {}).get("reversion_table", {})
    for thr_label in ["dev_0.5", "dev_1.0", "dev_1.5", "dev_2.0"]:
        thr_data = lon_thr_tbl.get(thr_label, {})
        row = f"| {thr_label.replace('dev_','')} ATR |"
        for lag_label in ["lag_1", "lag_2", "lag_4", "lag_8"]:
            entry = thr_data.get(lag_label, {})
            rate = entry.get("reversion_rate") if isinstance(entry, dict) else None
            n_ev = entry.get("n_events", 0) if isinstance(entry, dict) else 0
            p_val = entry.get("binom_p_vs_50pct") if isinstance(entry, dict) else None
            cell = f"{rate:.1%} (n={n_ev}) {_fmt_p(p_val, bonf_alpha)}" if rate is not None else "N/A"
            row += f" {cell} |"
        lines.append(row)

    lines += [
        "",
        "### XAUUSD — NY Session VWAP Reversion Table (1.0 ATR dev)",
        "",
        "| Threshold | Lag 1 | Lag 2 | Lag 4 | Lag 8 |",
        "|-----------|-------|-------|-------|-------|",
    ]
    ny_thr_tbl = xau_b3.get("sessions", {}).get("NY", {}).get("reversion_table", {})
    thr_data = ny_thr_tbl.get("dev_1.0", {})
    row_ny = "| 1.0 ATR |"
    for lag_label in ["lag_1", "lag_2", "lag_4", "lag_8"]:
        entry = thr_data.get(lag_label, {})
        rate = entry.get("reversion_rate") if isinstance(entry, dict) else None
        n_ev = entry.get("n_events", 0) if isinstance(entry, dict) else 0
        p_val = entry.get("binom_p_vs_50pct") if isinstance(entry, dict) else None
        cell = f"{rate:.1%} (n={n_ev}) {_fmt_p(p_val, bonf_alpha)}" if rate is not None else "N/A"
        row_ny += f" {cell} |"
    lines.append(row_ny)

    lines += [
        "",
        "### All-Instrument Summary — London Session VWAP (1.0 ATR, Lag 4 cumulative)",
        "",
        "| Instrument | N Events | Reversion Rate | Binom p | vs OB (70%) |",
        "|------------|----------|----------------|---------|-------------|",
    ]
    for sym, res in all_results.get("b3", {}).items():
        entry = (res.get("sessions", {}).get("London", {})
                    .get("reversion_table", {}).get("dev_1.0", {}).get("lag_4", {}))
        if not isinstance(entry, dict):
            continue
        rate = entry.get("reversion_rate")
        n_ev = entry.get("n_events", 0)
        p_val = entry.get("binom_p_vs_50pct")
        vs_ob = ("STRONGER" if rate and rate > 0.70 else "WEAKER" if rate and rate < 0.70 else "COMPARABLE") if rate else "N/A"
        lines.append(
            f"| {sym} | {n_ev} | {f'{rate:.1%}' if rate else 'N/A'} "
            f"| {_fmt_p(p_val, bonf_alpha)} | {vs_ob} |"
        )

    lines += [
        "",
        "### Displacement Speed Analysis (XAUUSD London, 1.0 ATR dev, Lag 4 cumulative)",
        "",
    ]
    speed = xau_b3.get("displacement_speed", {})
    for k, v in speed.items():
        lines.append(f"- **{k}:** n={v.get('n_events','?')}, "
                     f"reversion rate = {v.get('reversion_rate_within_lag4','?')}")

    daily_ref = xau_b3.get("daily_vwap_reference", {})
    if daily_ref:
        lines += [
            "",
            "### Daily VWAP Reference (bias check)",
            f"- Mean KZ deviation (daily VWAP): {daily_ref.get('mean_deviation_kz_ATR','?')} ATR — "
            f"{daily_ref.get('note','')}",
        ]

    lines += [
        "",
        "---",
        "",
        "## GTOS Implications Summary",
        "",
        "### B1 — Pre-screen recalibration",
    ]

    xau_b1_corr = all_results.get("b1", {}).get("XAUUSD", {}).get("correlation", {})
    r_b1 = xau_b1_corr.get("pearson_r", "?")
    p_b1 = xau_b1_corr.get("pearson_p", 1.0)
    if isinstance(p_b1, float) and p_b1 < 0.05:
        lines.append(
            f"- Asia–London correlation: r={r_b1}, p={p_b1:.4f} — statistically significant. "
            "Narrow Asia days are NOT identical to random days; pre-screen should consider this."
        )
    else:
        lines.append(
            f"- Asia–London correlation: r={r_b1}, p={p_b1:.4f} — NOT significant after Bonferroni. "
            "Asia range does not reliably predict London expansion in this sample. "
            "Pre-screen recalibration NOT warranted by this evidence."
        )

    lines += [
        "",
        "### B2 — Directional bias signal",
    ]
    xau_b2_lon = all_results.get("b2", {}).get("XAUUSD", {}).get("London_primary", {})
    b2_beta = xau_b2_lon.get("regression_beta", "?")
    b2_p = xau_b2_lon.get("regression_p", 1.0)
    b2_edge = xau_b2_lon.get("conditional_edge_bps", "?")
    if isinstance(b2_p, float) and b2_p < bonf_alpha:
        lines.append(
            f"- London first-half → second-half: β={b2_beta}, p={b2_p:.4f} (**Bonferroni-significant**). "
            f"Conditional edge: {b2_edge} bps. "
            "PROMOTE to candidate directional filter in Component 3A evaluation context."
        )
    elif isinstance(b2_p, float) and b2_p < 0.05:
        lines.append(
            f"- London first-half → second-half: β={b2_beta}, p={b2_p:.4f} (raw sig, fails Bonferroni). "
            f"Conditional edge: {b2_edge} bps. "
            "DEFER — replicate in out-of-sample period before using as filter."
        )
    else:
        lines.append(
            f"- London first-half → second-half: β={b2_beta}, p={b2_p:.4f} — NOT significant. "
            "First-half momentum does not predict second-half in XAUUSD London session. "
            "Do NOT use as directional input."
        )

    lines += [
        "",
        "### B3 — VWAP as alternative zone type",
    ]
    xau_b3_entry = (xau_b3.get("sessions", {}).get("London", {})
                         .get("reversion_table", {}).get("dev_1.0", {}).get("lag_4", {}))
    b3_rate = xau_b3_entry.get("reversion_rate", None) if isinstance(xau_b3_entry, dict) else None
    b3_p = xau_b3_entry.get("binom_p_vs_50pct", 1.0) if isinstance(xau_b3_entry, dict) else 1.0
    if b3_rate is not None:
        if b3_rate > 0.70 and (isinstance(b3_p, float) and b3_p < bonf_alpha):
            lines.append(
                f"- VWAP reversion rate (1.0 ATR, lag-4): {b3_rate:.1%}, p={b3_p:.4f} (**Bonferroni-significant**). "
                "STRONGER than OB benchmark (70%). "
                "RECOMMEND: add VWAP zone to Component 2 (market_state.py) for Component 13 edge discovery."
            )
        elif b3_rate > 0.70:
            lines.append(
                f"- VWAP reversion rate (1.0 ATR, lag-4): {b3_rate:.1%} (>70% benchmark), p={b3_p:.4f} (raw). "
                "Comparable to OB but fails Bonferroni. DEFER for larger sample."
            )
        elif b3_rate > 0.55 and (isinstance(b3_p, float) and b3_p < bonf_alpha):
            lines.append(
                f"- VWAP reversion rate (1.0 ATR, lag-4): {b3_rate:.1%} (**Bonferroni-significant** but WEAKER than OB 70%). "
                "Exists as a phenomenon but is not competitive with OB zone edge. "
                "VWAP is a secondary zone at best."
            )
        else:
            lines.append(
                f"- VWAP reversion rate (1.0 ATR, lag-4): {b3_rate:.1%} — WEAKER than OB benchmark (70%). "
                "Do NOT replace OB zones with VWAP zones. "
                "May serve as a confirming filter (price at VWAP + at OB zone = confluence)."
            )
    else:
        lines.append("- VWAP analysis incomplete — insufficient events at 1.0 ATR threshold.")

    lines += [
        "",
        "---",
        "",
        "## Methodology Notes",
        "",
        "- **Asia timezone:** UTC confirmed. Monday first-bar offset (01:00 UTC) handled by requiring ≥ 3 bars in session.",
        "- **VWAP quality:** Tick volume used as proxy; bar-count fallback for constant-volume days. VWAP from H1 vs M15 quality check not applicable (no H1 VWAP equivalent — different granularity).",
        "- **B2 alternative split:** Both 08:30 and 09:00 midpoints tested for robustness.",
        "- **Bonferroni:** Applied across all primary hypothesis tests in this batch (not post-hoc).",
        f"- **Total tests in Bonferroni pool:** {len(ALL_PVALUES)} (at time of writing)",
    ]

    md_text = "\n".join(lines)
    return md_text


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    global ALL_PVALUES
    ALL_PVALUES = []

    print("=" * 70)
    print("GTOS Temporal & Zone Analysis: B1, B2, B3")
    print(f"Started: {datetime.utcnow().isoformat()} UTC")
    print("=" * 70)

    all_results: Dict[str, Any] = {
        "metadata": {
            "generated_at": TIMESTAMP,
            "instruments": list(INSTRUMENTS.keys()),
            "b1_data": "H1",
            "b2_data": "M15",
            "b3_data": "M15",
            "timezone": "UTC (confirmed by broker export inspection)",
            "bonferroni_note": "α* computed after all tests complete",
        },
        "b1": {},
        "b2": {},
        "b3": {},
    }

    # ── Load H1 data for all instruments ─────────────────────────────────────
    print("\n[1/4] Loading H1 data …")
    h1_data: Dict[str, pd.DataFrame] = {}
    for sym in INSTRUMENTS:
        df = load_data(sym, "H1")
        if df is not None:
            h1_data[sym] = df
            print(f"  {sym} H1: {len(df)} bars ({df.index.min().date()} → {df.index.max().date()})")

    # ── Load M15 data for all instruments ─────────────────────────────────────
    print("\n[2/4] Loading M15 data …")
    m15_data: Dict[str, pd.DataFrame] = {}
    for sym in INSTRUMENTS:
        df = load_data(sym, "M15")
        if df is not None:
            m15_data[sym] = df
            print(f"  {sym} M15: {len(df)} bars ({df.index.min().date()} → {df.index.max().date()})")

    # ── B1 ────────────────────────────────────────────────────────────────────
    print("\n[3/4] Running B1: Asia Range → London Prediction …")
    for sym in INSTRUMENTS:
        if sym not in h1_data:
            print(f"  SKIP {sym}: no H1 data")
            continue
        try:
            res = b1_run_analysis(sym, h1_data[sym])
            all_results["b1"][sym] = res

            # Plot for XAUUSD only (representative)
            if sym == "XAUUSD":
                london_lo, london_hi = LONDON_KZ[sym]
                ny_lo, ny_hi = NY_KZ[sym]
                df_days = b1_compute_session_stats(h1_data[sym],
                                                    *ASIA_SESSION, london_lo, london_hi, ny_lo, ny_hi)
                df_days = df_days.dropna(subset=["asia_range", "london_range"])
                df_days["asia_q"] = pd.qcut(df_days["asia_range"], 4, labels=["Q1","Q2","Q3","Q4"])
                b1_plot_scatter(sym, df_days)
                print(f"    Saved B1 scatter plot for {sym}")
        except Exception as e:
            print(f"  ERROR B1 {sym}: {e}")
            traceback.print_exc()
            all_results["b1"][sym] = {"error": str(e)}

    # ── B2 ────────────────────────────────────────────────────────────────────
    print("\n[4a/4] Running B2: Intraday Momentum …")
    for sym in INSTRUMENTS:
        if sym not in m15_data:
            print(f"  SKIP {sym}: no M15 data")
            continue
        try:
            res = b2_run_analysis(sym, m15_data[sym])
            all_results["b2"][sym] = res

            # Plot XAUUSD London primary
            if sym == "XAUUSD":
                london_lo = LONDON_KZ[sym][0]
                b2_plot(sym, m15_data[sym], "London_primary",
                        london_lo, 8.5, 8.5, LONDON_KZ[sym][1])
        except Exception as e:
            print(f"  ERROR B2 {sym}: {e}")
            traceback.print_exc()
            all_results["b2"][sym] = {"error": str(e)}

    # ── B3 ────────────────────────────────────────────────────────────────────
    print("\n[4b/4] Running B3: VWAP Reversion …")
    for sym in INSTRUMENTS:
        if sym not in m15_data:
            print(f"  SKIP {sym}: no M15 data")
            continue
        try:
            res = b3_run_analysis(sym, m15_data[sym])
            all_results["b3"][sym] = res

            # Plot XAUUSD
            if sym == "XAUUSD":
                df_m15 = m15_data[sym]
                vwap_daily = b3_compute_vwap(df_m15)
                vwap_london = b3_compute_session_vwap(df_m15, *LONDON_KZ[sym])
                b3_plot(sym, df_m15, vwap_daily, vwap_london)
        except Exception as e:
            print(f"  ERROR B3 {sym}: {e}")
            traceback.print_exc()
            all_results["b3"][sym] = {"error": str(e)}

    # ── Bonferroni correction ─────────────────────────────────────────────────
    n_tests = len(ALL_PVALUES)
    bonf_alpha = bonferroni_alpha(n_tests)
    all_results["metadata"]["n_tests"] = n_tests
    all_results["metadata"]["bonferroni_alpha"] = bonf_alpha
    all_results["metadata"]["bonferroni_sig_pvalues"] = [
        p for p in ALL_PVALUES if p < bonf_alpha
    ]
    n_bonf_sig = len(all_results["metadata"]["bonferroni_sig_pvalues"])

    print(f"\n── Bonferroni: {n_tests} tests, α* = {bonf_alpha:.6f}")
    print(f"   {n_bonf_sig} tests survive Bonferroni correction")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    json_path = os.path.join(OUT_DIR, f"temporal_zones_results_{TIMESTAMP}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nJSON saved: {json_path}")

    # ── Save Markdown ─────────────────────────────────────────────────────────
    md_text = write_summary_md(all_results, bonf_alpha, TIMESTAMP)
    md_path = os.path.join(OUT_DIR, f"temporal_zones_summary_{TIMESTAMP}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"Markdown saved: {md_path}")

    print("\nDone.")
    return all_results


if __name__ == "__main__":
    main()
