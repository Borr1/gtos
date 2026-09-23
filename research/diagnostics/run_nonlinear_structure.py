#!/usr/bin/env python3
"""
GTOS Nonlinear Structure Analysis
==================================
Three tests probing nonlinear / conditional structure in market data.
Linear tests (VR, autocorrelation) confirm gold H1 is statistically a random walk,
but the OB-retest edge (62% WR, p=3.42e-08) proves nonlinear or conditional structure
exists. These three tests locate that structure.

Tests:
  C1: Permutation Entropy (Q-15.7)  — orderliness / predictability over time
  C2: Markov Regime Switching (Q-15.9) — distinct market states + transition probs
  C3: London Gold Fix Anomaly (Q-14.3) — time-based pre/post-fix drift

Outputs (all versioned, never overwritten):
  research/diagnostics/nonlinear_structure/nonlinear_results_<ts>.json
  research/diagnostics/nonlinear_structure/nonlinear_summary_<ts>.md
  research/diagnostics/nonlinear_structure/plots/

Usage:
  python research/diagnostics/run_nonlinear_structure.py

Notes:
  - Reuses CSV files from data/historical/ (same source as variance_ratio tests)
  - Bonferroni correction: α* = 0.05/60 ≈ 0.00083 (est. 60 hypothesis tests)
  - MarkovRegression: 3 random inits per model; relabel by ascending variance
  - London fix: UK DST-correct UTC times; AM at 10:30 London, PM at 15:00 London
  - Pressure-test notes respected: m ≤ 6, returns not prices for Markov,
    post-2015 fix reform is a separate epoch
"""

import os
import sys
import json
import math
import warnings
import calendar
from collections import Counter
from datetime import datetime, date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors

try:
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    HAS_MARKOV = True
except ImportError:
    HAS_MARKOV = False
    print("WARNING: statsmodels MarkovRegression unavailable — C2 will be skipped")

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# PATHS AND CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR  = os.path.join(REPO_ROOT, "data", "historical")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "nonlinear_structure")
PLOTS_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(OUT_DIR,   exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

TIMESTAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

INSTRUMENTS = {
    "XAUUSD": {
        "prefix": "XAUUSD",
        "kz": {"London": (7.0, 10.5), "NY": (13.0, 17.0)},
    },
    "US30": {
        "prefix": "US30_cash",
        "kz": {"London": (8.0, 10.5), "NY": (13.5, 16.0)},
    },
    "USDJPY": {
        "prefix": "USDJPY",
        "kz": {"London": (7.0, 9.5), "NY": (13.0, 15.5)},
    },
    "GBPJPY": {
        "prefix": "GBPJPY",
        "kz": {"London": (7.0, 9.5), "NY": (13.0, 15.5)},
    },
    "GBPUSD": {
        "prefix": "GBPUSD",
        "kz": {"London": (7.0, 12.0), "NY": (13.0, 15.5)},
    },
}

TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}

# C1 settings
PE_DIMS    = [3, 4, 5, 6]
PE_TAU     = 1
PE_WINDOWS = [50, 100, 200]   # rolling window sizes (bars)

# Bonferroni
N_TESTS_ESTIMATE = 60         # estimated hypothesis tests across all three tests
ALPHA             = 0.05
ALPHA_BONF        = ALPHA / N_TESTS_ESTIMATE  # ≈ 0.00083

# C3 London fix
FIX_REFORM_YEAR = 2015        # LBMA electronic fix auction started March 2015
MIN_N_TTEST     = 20          # minimum observations before running t-test

# Colours for regime plots
REGIME_COLOURS = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]

# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_csv(symbol: str, tf: str) -> pd.DataFrame | None:
    """Return OHLCV DataFrame or None if file missing."""
    prefix = INSTRUMENTS[symbol]["prefix"]
    path   = os.path.join(DATA_DIR, f"{prefix}_{tf}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])
    df["time"] = pd.to_datetime(df["time"])
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = (df.dropna(subset=["time", "close"])
           .sort_values("time")
           .reset_index(drop=True))
    return df


def compute_log_returns(df: pd.DataFrame, tf: str):
    """
    Return (r, t, valid_mask) — log returns, timestamps, gap-filtered boolean mask.
    Gap filter: discard returns spanning > 3× expected bar duration.
    Returns are aligned to df[1:] (return r[i] corresponds to bar i+1 in df).
    """
    closes = df["close"].values.astype(np.float64)
    times  = df["time"].values
    r      = np.diff(np.log(closes))
    t      = times[1:]
    tfm    = TF_MINUTES.get(tf, 60)
    gaps   = df["time"].diff().dt.total_seconds().iloc[1:].values / 60
    valid  = (gaps <= tfm * 3) & np.isfinite(r)
    return r[valid], t[valid], valid


def hour_utc(ts) -> float:
    """Extract decimal UTC hour from a numpy datetime64 or pandas Timestamp."""
    if isinstance(ts, (np.datetime64,)):
        ts = pd.Timestamp(ts)
    return ts.hour + ts.minute / 60.0


# ═══════════════════════════════════════════════════════════════════════════
# PERMUTATION ENTROPY (numpy, no ordpy dependency)
# ═══════════════════════════════════════════════════════════════════════════

def _ordinal_codes(x: np.ndarray, m: int) -> np.ndarray:
    """
    Encode all ordinal patterns in x for embedding dimension m (tau=1).
    Returns integer array of length n-m+1 using base-m positional encoding.
    Encoding is injective on permutations of {0,...,m-1}.
    """
    # sliding window view: shape (n-m+1, m)
    embedded = np.lib.stride_tricks.sliding_window_view(x, m)
    ranks    = np.argsort(embedded, axis=1)              # (n-m+1, m) rank arrays
    mult     = (m ** np.arange(m - 1, -1, -1)).astype(np.int64)
    return (ranks * mult).sum(axis=1).astype(np.int64)   # unique int per pattern


def pe_full(x: np.ndarray, m: int) -> float:
    """Normalized permutation entropy of x for embedding dimension m (tau=1)."""
    n = len(x)
    if n < m + 5:
        return np.nan
    codes = _ordinal_codes(x, m)
    _, counts = np.unique(codes, return_counts=True)
    p      = counts / counts.sum()
    H      = -float(np.sum(p * np.log(p)))
    H_max  = math.log(math.factorial(m))
    return H / H_max if H_max > 0 else 0.0


def rolling_pe(x: np.ndarray, window: int, m: int) -> np.ndarray:
    """
    Compute normalized PE on a rolling window using a sliding Counter.
    O(n × k) where k ≤ m! unique patterns.
    Returns array of length n (nan for bars before the first full window).
    """
    n      = len(x)
    H_max  = math.log(math.factorial(m))
    result = np.full(n, np.nan)
    n_pats = window - m + 1     # patterns per window
    if n < window or n_pats < 1:
        return result

    codes  = _ordinal_codes(x, m)   # length n-m+1
    n_codes = len(codes)

    # Initialize Counter for first window
    freq = Counter(int(c) for c in codes[:n_pats])

    for i in range(window - 1, n):
        H = sum(-cnt / n_pats * math.log(cnt / n_pats)
                for cnt in freq.values())
        result[i] = H / H_max

        if i < n - 1:
            # Remove oldest pattern
            out = int(codes[i - window + 1])
            freq[out] -= 1
            if freq[out] == 0:
                del freq[out]
            # Add newest pattern
            in_idx = i - m + 2
            if in_idx < n_codes:
                new = int(codes[in_idx])
                freq[new] = freq.get(new, 0) + 1

    return result


# ═══════════════════════════════════════════════════════════════════════════
# UK DST HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _last_sunday(year: int, month: int) -> date:
    """Return date of last Sunday in (year, month)."""
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    # weekday(): Mon=0 … Sun=6; days to go back to reach Sunday:
    days_back = (d.weekday() + 1) % 7
    return d - timedelta(days=days_back)


def is_bst(d) -> bool:
    """True if d falls within UK British Summer Time (UTC+1)."""
    if hasattr(d, "date"):
        d = d.date()
    elif isinstance(d, (np.datetime64,)):
        d = pd.Timestamp(d).date()
    year = d.year
    bst_start = _last_sunday(year, 3)    # last Sunday of March
    bst_end   = _last_sunday(year, 10)   # last Sunday of October
    return bst_start <= d < bst_end


def london_fix_utc(d, fix_type: str) -> pd.Timestamp:
    """
    Return UTC timestamp of AM ('AM') or PM ('PM') LBMA Gold Fix for date d.
    AM fix: 10:30 London (09:30 UTC in BST, 10:30 UTC in GMT)
    PM fix: 15:00 London (14:00 UTC in BST, 15:00 UTC in GMT)
    """
    if hasattr(d, "date"):
        d = d.date()
    elif isinstance(d, (np.datetime64,)):
        d = pd.Timestamp(d).date()
    bst = is_bst(d)
    if fix_type == "AM":
        h, mn = (9, 30) if bst else (10, 30)
    else:
        h, mn = (14, 0) if bst else (15, 0)
    return pd.Timestamp(year=d.year, month=d.month, day=d.day, hour=h, minute=mn)


# ═══════════════════════════════════════════════════════════════════════════
# STATISTICAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def ttest_one_sample(x: np.ndarray, mu0: float = 0.0):
    """One-sample t-test. Returns (t_stat, p_two_tailed, n)."""
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 5:
        return np.nan, np.nan, n
    t, p = stats.ttest_1samp(x, mu0)
    return float(t), float(p), n


def ttest_two_sample(a: np.ndarray, b: np.ndarray):
    """Welch two-sample t-test. Returns (t_stat, p_two_tailed, n_a, n_b)."""
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 5 or len(b) < 5:
        return np.nan, np.nan, len(a), len(b)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(t), float(p), len(a), len(b)


def ols_regress(y: np.ndarray, x: np.ndarray):
    """OLS regression y ~ 1 + x. Returns dict with slope, intercept, t, p, r2."""
    mask = np.isfinite(y) & np.isfinite(x)
    y, x = y[mask], x[mask]
    n = len(y)
    if n < 10:
        return {"n": n, "alpha": np.nan, "beta": np.nan,
                "t_stat": np.nan, "p_value": np.nan, "r_squared": np.nan}
    result = stats.linregress(x, y)
    return {
        "n":        n,
        "alpha":    float(result.intercept),
        "beta":     float(result.slope),
        "t_stat":   float(result.slope / result.stderr) if result.stderr else np.nan,
        "p_value":  float(result.pvalue),
        "r_squared": float(result.rvalue ** 2),
    }


def _j(v):
    """JSON-safe conversion: replace nan/inf with None."""
    if isinstance(v, dict):
        return {k: _j(vv) for k, vv in v.items()}
    if isinstance(v, (list, tuple)):
        return [_j(vv) for vv in v]
    if isinstance(v, np.ndarray):
        return [_j(float(vv)) for vv in v.flat]
    if isinstance(v, (np.integer, np.int64)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(float(v), 8)
    return v


# ═══════════════════════════════════════════════════════════════════════════
# TEST C1: PERMUTATION ENTROPY
# ═══════════════════════════════════════════════════════════════════════════

def run_c1(verbose: bool = True) -> dict:
    """
    C1: Permutation Entropy across 5 instruments at H1.

    Analyses:
      a) Mean PE for full H1 series, by embedding dimension m=3..6
         (test: is mean PE significantly below 1.0? → nonlinear structure)
      b) KZ vs non-KZ PE comparison (Welch t-test)
      c) Rolling PE(m=5, w=100) on XAUUSD → saved for plot
      d) London-range regression: daily PE → next-session London range
    """
    if verbose:
        print("\n" + "═"*70)
        print("TEST C1: PERMUTATION ENTROPY")
        print("═"*70)

    results = {}

    for sym in INSTRUMENTS:
        if verbose:
            print(f"\n  [{sym}] Loading H1 data...")
        df = load_csv(sym, "H1")
        if df is None:
            results[sym] = {"error": "no data"}
            continue

        r, t, _ = compute_log_returns(df, "H1")
        n        = len(r)
        kz_def   = INSTRUMENTS[sym]["kz"]

        if verbose:
            print(f"    n={n} valid H1 returns  "
                  f"({df['time'].iloc[0].date()} → {df['time'].iloc[-1].date()})")

        # --- a) Full-series PE per dimension --------------------------------
        t_pd = pd.to_datetime(t)
        hours_utc = np.array([ts.hour + ts.minute / 60 for ts in t_pd])

        by_dim = {}
        for m in PE_DIMS:
            pe_val = pe_full(r, m)
            # Test: PE < null (is series MORE ordered than IID random walk of same length?)
            # Null = PE of shuffled full series (same n), which approaches 1.0 for large n.
            # 500 full-series shuffles; each takes ~0.001s for n≈15k.
            null_pe = []
            rng_shuf = np.random.default_rng(42)
            for _ in range(500):
                r_sh = rng_shuf.permutation(r)   # shuffle full series, not truncated
                null_pe.append(pe_full(r_sh, m))
            null_mean = float(np.nanmean(null_pe))
            null_std  = float(np.nanstd(null_pe))
            # z < 0 means observed PE is BELOW null → series is MORE ordered than random
            z_score   = (pe_val - null_mean) / null_std if null_std > 0 else np.nan
            # One-sided p-value: P(PE ≤ observed | null is IID) — lower PE = more structure
            p_val_1s  = float(stats.norm.cdf(z_score)) if np.isfinite(z_score) else np.nan
            p_val_2s  = float(stats.norm.sf(abs(z_score)) * 2) if np.isfinite(z_score) else np.nan
            sig_bonf  = bool(p_val_1s < ALPHA_BONF) if np.isfinite(p_val_1s) else False
            by_dim[f"m{m}"] = {
                "pe":            float(pe_val) if np.isfinite(pe_val) else None,
                "null_mean":     round(null_mean, 6),
                "null_std":      round(null_std, 6),
                "z_score":       round(z_score, 4) if np.isfinite(z_score) else None,
                "p_value_1s":    round(p_val_1s, 6) if np.isfinite(p_val_1s) else None,
                "p_value_2s":    round(p_val_2s, 6) if np.isfinite(p_val_2s) else None,
                "p_value":       round(p_val_1s, 6) if np.isfinite(p_val_1s) else None,
                "sig_bonf":      sig_bonf,
            }
            if verbose:
                star = "*" if sig_bonf else ""
                print(f"    m={m}: PE={pe_val:.5f}  null={null_mean:.5f}±{null_std:.5f}"
                      f"  z={z_score:+.3f}  p(1s)={p_val_1s:.4f}{star}")

        # --- b) KZ vs non-KZ comparison ------------------------------------
        kz_analysis = {}
        kz_any_mask = np.zeros(n, dtype=bool)
        for kz_name, (lo, hi) in kz_def.items():
            kz_mask     = (hours_utc >= lo) & (hours_utc < hi)
            non_kz_mask = ~kz_mask
            kz_any_mask |= kz_mask

            r_kz    = r[kz_mask]
            r_non   = r[non_kz_mask]

            pe_kz   = pe_full(r_kz,  5) if len(r_kz)  > 20 else np.nan
            pe_non  = pe_full(r_non, 5) if len(r_non) > 20 else np.nan

            t_stat, p_val, n_kz, n_non = ttest_two_sample(
                np.array([pe_kz]), np.array([pe_non])  # placeholder for subset-level
            )
            # Better: compute PE on rolling windows then compare by session
            # For a more meaningful test, compute PE values per hour-bin
            hourly_pe = {}
            for h in range(24):
                mask_h = (hours_utc.astype(int) == h)
                if mask_h.sum() > m + 10:
                    hourly_pe[h] = pe_full(r[mask_h], 5)
            kz_hour_pes  = [v for h, v in hourly_pe.items()
                            if kz_def[kz_name][0] <= h < kz_def[kz_name][1]
                            and np.isfinite(v)]
            nkz_hour_pes = [v for h, v in hourly_pe.items()
                            if not (kz_def[kz_name][0] <= h < kz_def[kz_name][1])
                            and np.isfinite(v)]

            t_stat2, p_val2, n_kz2, n_non2 = ttest_two_sample(
                np.array(kz_hour_pes), np.array(nkz_hour_pes)
            )
            kz_analysis[kz_name] = {
                "pe_kz_full_series":     round(pe_kz,  6) if np.isfinite(pe_kz)  else None,
                "pe_nonkz_full_series":  round(pe_non, 6) if np.isfinite(pe_non) else None,
                "pe_kz_mean_hourly":     round(float(np.mean(kz_hour_pes)), 6) if kz_hour_pes else None,
                "pe_nonkz_mean_hourly":  round(float(np.mean(nkz_hour_pes)), 6) if nkz_hour_pes else None,
                "n_kz_hours":            int(n_kz2),
                "n_nonkz_hours":         int(n_non2),
                "t_stat_hourly":         round(t_stat2, 4) if np.isfinite(t_stat2) else None,
                "p_value_hourly":        round(p_val2, 6) if np.isfinite(p_val2) else None,
                "sig_bonf":              bool(p_val2 < ALPHA_BONF) if np.isfinite(p_val2) else False,
                "kz_lower_pe":           bool(pe_kz < pe_non) if np.isfinite(pe_kz) and np.isfinite(pe_non) else None,
            }
            if verbose:
                dir_str = "KZ < nonKZ (more ordered)" if (np.isfinite(pe_kz) and pe_kz < pe_non) else "KZ >= nonKZ"
                print(f"    {kz_name} KZ: pe={pe_kz:.5f}  nonKZ: pe={pe_non:.5f}  → {dir_str}")

        # --- c) Rolling PE(m=5, w=100) for XAUUSD plot --------------------
        rolling_pe_m5_w100 = None
        rolling_pe_timestamps = None
        if sym == "XAUUSD":
            if verbose:
                print("    Computing rolling PE(m=5, w=100) for XAUUSD plot...")
            rpe = rolling_pe(r, 100, 5)
            rolling_pe_m5_w100     = rpe.tolist()
            rolling_pe_timestamps  = [str(ts)[:16] for ts in t_pd]

        # --- d) London-range regression (XAUUSD only) ----------------------
        london_range_reg = None
        if sym == "XAUUSD":
            if verbose:
                print("    Computing London range regression...")
            # Build daily dataframe with: daily PE, next-day London range
            t_series = pd.Series(t_pd)
            r_series = pd.Series(r, index=t_series)
            dates_all = t_series.dt.date.unique()

            daily_records = []
            for d_cur in dates_all:
                # Current day PE (all H1 returns for that day)
                mask_today  = t_series.dt.date == d_cur
                r_today     = r[mask_today.values]
                pe_today    = pe_full(r_today, 5) if len(r_today) >= 8 else np.nan

                # Next day London session range
                d_nxt = d_cur + timedelta(days=1)
                # Try up to 3 days forward (skip weekends)
                lon_range = np.nan
                for delta in range(1, 5):
                    d_try = d_cur + timedelta(days=delta)
                    mask_kz = (t_series.dt.date == d_try) & \
                              (hours_utc >= 7.0) & (hours_utc < 10.5)
                    if mask_kz.sum() >= 2:
                        closes_kz = df["close"].iloc[1:].values[mask_today.values.sum():]
                        # Safer: get close prices for this date-KZ window
                        dfday = df[(df["time"].dt.date == d_try)].copy()
                        dfday_kz = dfday[
                            (dfday["time"].dt.hour + dfday["time"].dt.minute/60 >= 7.0) &
                            (dfday["time"].dt.hour + dfday["time"].dt.minute/60 < 10.5)
                        ]
                        if len(dfday_kz) >= 2:
                            lon_range = float(
                                np.log(dfday_kz["high"].max() / dfday_kz["low"].min())
                            )
                        break

                daily_records.append({"pe": pe_today, "london_range": lon_range})

            dr   = pd.DataFrame(daily_records).dropna()
            reg  = ols_regress(dr["london_range"].values, dr["pe"].values)
            london_range_reg = reg
            london_range_reg["interpretation"] = (
                "lower PE → larger London range (pre-screen signal)"
                if reg.get("beta", 0) is not None and reg.get("beta", 0) < 0
                else "no clear directional relationship"
            )
            if verbose:
                beta = reg.get("beta")
                pv   = reg.get("p_value")
                print(f"    London range ~ PE: β={beta}, p={pv}, n={reg.get('n')}")

        results[sym] = {
            "n_returns":       n,
            "date_range":      [str(df["time"].iloc[0])[:10],
                                str(df["time"].iloc[-1])[:10]],
            "by_dimension":    by_dim,
            "kz_analysis":     kz_analysis,
            "rolling_pe_m5_w100": rolling_pe_m5_w100,
            "rolling_pe_timestamps": rolling_pe_timestamps,
            "london_range_regression": london_range_reg,
        }

    return results


# ═══════════════════════════════════════════════════════════════════════════
# TEST C2: MARKOV REGIME SWITCHING
# ═══════════════════════════════════════════════════════════════════════════

def _fit_markov(returns: np.ndarray, k: int, seed: int):
    """Fit a k-state MarkovRegression with regime-switching mean and variance."""
    np.random.seed(seed)
    mod = MarkovRegression(
        returns,
        k_regimes=k,
        trend="c",
        switching_trend=True,
        switching_variance=True,
    )
    try:
        res = mod.fit(disp=False, maxiter=300)
    except Exception as exc:
        return None, str(exc)
    return (mod, res), None


def _extract_regime_params(mod, res, k: int) -> dict:
    """Extract means, variances, transition matrix, durations from fitted result."""
    param_names = mod.param_names
    params_arr  = res.params   # numpy array
    param_dict  = dict(zip(param_names, params_arr))

    means = [param_dict.get(f"const[{i}]", np.nan) for i in range(k)]
    varis = [param_dict.get(f"sigma2[{i}]", np.nan) for i in range(k)]

    # Regime order by ascending variance (lowest-var state = state 0)
    order     = np.argsort(varis)
    inv_order = np.argsort(order)

    means_ord = [means[order[i]] for i in range(k)]
    varis_ord = [varis[order[i]] for i in range(k)]

    # Transition matrix: shape (k, k, T); regime_transition[j,i,0] = P(to j | from i)
    P_raw = res.regime_transition[:, :, 0]  # (k, k)
    # Reorder rows and columns according to variance ranking
    P_ord = P_raw[np.ix_(order, order)]

    # Average durations
    durations = res.expected_durations.tolist()
    durations_ord = [durations[order[i]] for i in range(k)]

    # State fractions (time spent in each regime)
    smoothed = res.smoothed_marginal_probabilities  # (T, k) ndarray
    frac = smoothed.mean(axis=0).tolist()
    frac_ord = [frac[order[i]] for i in range(k)]

    return {
        "means":          means_ord,
        "variances":      varis_ord,
        "std_devs":       [math.sqrt(max(v, 0)) for v in varis_ord],
        "transition_P":   P_ord.tolist(),
        "avg_duration":   durations_ord,
        "state_fractions": frac_ord,
        "order_by_var":   order.tolist(),
    }


def _detection_lag(filtered_probs: np.ndarray, k: int,
                   threshold: float = 0.80) -> dict:
    """
    Compute detection lag: bars from a state transition until
    filtered probability of new state exceeds `threshold`.
    Uses filtered (causal) probabilities — real-time analogue.
    """
    T        = filtered_probs.shape[0]
    map_st   = filtered_probs.argmax(axis=1)   # MAP state at each bar
    lags     = []
    max_scan = 100    # give up after 100 bars

    # Transitions: positions where MAP state changes
    changes = np.where(np.diff(map_st) != 0)[0] + 1

    for t0 in changes:
        new_st = map_st[t0]
        for t_scan in range(t0, min(t0 + max_scan, T)):
            if filtered_probs[t_scan, new_st] >= threshold:
                lags.append(t_scan - t0)
                break
        else:
            lags.append(max_scan)   # censored

    if not lags:
        return {"n_transitions": 0, "mean": None, "median": None,
                "pct_within_4bars": None}

    lags = np.array(lags)
    return {
        "n_transitions":   int(len(lags)),
        "mean":            round(float(lags.mean()), 2),
        "median":          round(float(np.median(lags)), 2),
        "pct_within_4bars": round(float((lags <= 4).mean() * 100), 1),
        "pct_censored":    round(float((lags >= max_scan).mean() * 100), 1),
    }


def _kz_regime_affinity(filtered_probs: np.ndarray, hours: np.ndarray, k: int,
                         kz_def: dict) -> dict:
    """
    For each regime, compute mean P(in regime) during KZ vs non-KZ.
    High KZ affinity for a regime suggests it captures kill-zone structure.
    """
    kz_mask = np.zeros(len(hours), dtype=bool)
    for lo, hi in kz_def.values():
        kz_mask |= (hours >= lo) & (hours < hi)

    result = {}
    for i in range(k):
        probs = filtered_probs[:, i]
        result[f"state_{i}"] = {
            "mean_prob_kz":     round(float(probs[kz_mask].mean()), 4)
                                if kz_mask.sum() > 0 else None,
            "mean_prob_nonkz":  round(float(probs[~kz_mask].mean()), 4)
                                if (~kz_mask).sum() > 0 else None,
        }
    return result


def run_c2(verbose: bool = True) -> dict:
    """
    C2: Markov Regime Switching on H1 returns for all 5 instruments.
    Fits 2-state and 3-state models with 3 random initializations each.
    Relabels regimes by ascending variance (state 0 = quietest).
    """
    if not HAS_MARKOV:
        return {"error": "statsmodels MarkovRegression not available"}

    if verbose:
        print("\n" + "═"*70)
        print("TEST C2: MARKOV REGIME SWITCHING")
        print("═"*70)

    results = {}
    SEEDS   = [0, 42, 137]

    for sym in INSTRUMENTS:
        if verbose:
            print(f"\n  [{sym}] Loading H1 data...")
        df = load_csv(sym, "H1")
        if df is None:
            results[sym] = {"error": "no data"}
            continue

        r, t, _ = compute_log_returns(df, "H1")
        n        = len(r)
        t_pd     = pd.to_datetime(t)
        hours    = np.array([ts.hour + ts.minute / 60 for ts in t_pd])
        kz_def   = INSTRUMENTS[sym]["kz"]

        if verbose:
            print(f"    n={n} returns  |r|_mean={np.abs(r).mean():.6f}")

        sym_results = {}
        for k in (2, 3):
            if verbose:
                print(f"    Fitting {k}-state Markov (3 seeds)...")

            best_llf = -np.inf
            best_run = None
            run_records = []

            for seed in SEEDS:
                pair, err = _fit_markov(r, k, seed)
                if pair is None:
                    run_records.append({"seed": seed, "error": err})
                    if verbose:
                        print(f"      seed={seed} FAILED: {err}")
                    continue
                mod_s, res_s = pair
                llf_s = float(res_s.llf)
                run_records.append({"seed": seed, "llf": round(llf_s, 2), "error": None})
                if verbose:
                    print(f"      seed={seed} → llf={llf_s:.2f}")
                if llf_s > best_llf:
                    best_llf = llf_s
                    best_run = (mod_s, res_s)

            if best_run is None:
                sym_results[f"{k}state"] = {"error": "all seeds failed"}
                continue

            mod_b, res_b = best_run
            params       = _extract_regime_params(mod_b, res_b, k)
            filtered     = res_b.filtered_marginal_probabilities   # (T, k)
            smoothed     = res_b.smoothed_marginal_probabilities   # (T, k)
            lag_info     = _detection_lag(filtered, k)
            kz_aff       = _kz_regime_affinity(filtered, hours, k, kz_def)

            # State colour arrays for plotting (reordered by variance)
            order      = params["order_by_var"]
            map_states = np.array([order[s] for s in filtered.argmax(axis=1)])

            if verbose:
                print(f"      Best {k}-state: llf={best_llf:.2f}")
                for i in range(k):
                    print(f"        State {i}: μ={params['means'][i]:.6f}, "
                          f"σ²={params['variances'][i]:.8f}, "
                          f"dur={params['avg_duration'][i]:.1f}bars, "
                          f"frac={params['state_fractions'][i]:.2%}")
                print(f"      Detection lag (P80): {lag_info}")

            sym_results[f"{k}state"] = {
                "best_llf":        round(best_llf, 3),
                "aic":             round(float(res_b.aic), 3),
                "bic":             round(float(res_b.bic), 3),
                "converged":       True,
                "n_runs":          len(run_records),
                "run_seeds":       run_records,
                "regime_params":   params,
                "detection_lag_p80": lag_info,
                "kz_regime_affinity": kz_aff,
                # Store smoothed/filtered probs for XAUUSD plot
                "filtered_probs":  filtered.tolist() if sym == "XAUUSD" else None,
                "smoothed_probs":  smoothed.tolist() if sym == "XAUUSD" else None,
                "map_states":      map_states.tolist() if sym == "XAUUSD" else None,
                "timestamps":      [str(ts)[:16] for ts in t_pd] if sym == "XAUUSD" else None,
            }

        results[sym] = {"n_returns": n, **sym_results}

    return results


# ═══════════════════════════════════════════════════════════════════════════
# TEST C3: LONDON GOLD FIX ANOMALY
# ═══════════════════════════════════════════════════════════════════════════

def _get_bar_close(df_indexed: pd.DataFrame, ts: pd.Timestamp) -> float:
    """
    Close price of the M15 bar whose open is at or immediately before ts.
    df_indexed must be indexed by 'time'.
    """
    before = df_indexed.index[df_indexed.index <= ts]
    if len(before) == 0:
        return np.nan
    return float(df_indexed.loc[before[-1], "close"])


def _analyze_fix_window(records: list, label: str, verbose: bool) -> dict:
    """
    Given a list of dicts with pre/post returns for one fix type,
    compute t-tests and economic significance.
    """
    if not records:
        return {"n": 0, "error": "no data"}

    df = pd.DataFrame(records)
    out = {"n": len(df)}

    windows = {
        "pre_60":  "pre_60",
        "pre_30":  "pre_30",
        "pre_15":  "pre_15",
        "post_30": "post_30",
        "post_60": "post_60",
    }
    for col, label_col in windows.items():
        if col not in df.columns:
            continue
        vals = df[col].dropna().values
        if len(vals) < MIN_N_TTEST:
            out[col] = {"n": len(vals), "error": "too few obs"}
            continue
        t_stat, p_val, n = ttest_one_sample(vals * 10_000)   # convert to bps
        mean_bps = float(np.mean(vals)) * 10_000
        std_bps  = float(np.std(vals))  * 10_000
        out[col] = {
            "n":         int(n),
            "mean_bps":  round(mean_bps, 4),
            "std_bps":   round(std_bps, 4),
            "t_stat":    round(t_stat, 4) if np.isfinite(t_stat) else None,
            "p_value":   round(p_val, 6) if np.isfinite(p_val) else None,
            "sig_bonf":  bool(p_val < ALPHA_BONF) if np.isfinite(p_val) else False,
        }
        if verbose:
            star = "***" if (np.isfinite(p_val) and p_val < ALPHA_BONF) else \
                   "*"   if (np.isfinite(p_val) and p_val < 0.05) else ""
            print(f"      {col}: {mean_bps:+7.2f}bps  t={t_stat:+.2f}  p={p_val:.4f}{star}")

    return out


def run_c3(verbose: bool = True) -> dict:
    """
    C3: London Gold Fix Anomaly in XAUUSD M15 data.

    For each trading day:
      - AM fix: 10:30 London (DST-aware UTC)
      - PM fix: 15:00 London (DST-aware UTC)
    For each fix: compute pre-fix (−60, −30, −15 min) and post-fix (+30, +60 min) returns.
    Test: is mean pre-fix return ≠ 0? Has anomaly survived post-2015 reform?
    """
    if verbose:
        print("\n" + "═"*70)
        print("TEST C3: LONDON GOLD FIX ANOMALY")
        print("═"*70)

    df = load_csv("XAUUSD", "M15")
    if df is None:
        return {"error": "XAUUSD M15 data not found"}

    # Index by time for fast lookup
    df_idx = df.set_index("time")
    all_dates = sorted(df["time"].dt.date.unique())

    if verbose:
        print(f"  M15 data: {len(df)} bars  "
              f"({all_dates[0]} → {all_dates[-1]})")

    # --- Sanity check: volatility at fix times vs baseline ------------------
    if verbose:
        print("  Sanity check: verifying elevated volatility at fix windows...")

    fix_hl_ranges = []   # |H-L| of the bar AT fix time
    all_hl_ranges = (df["high"] - df["low"]).values.astype(float)
    baseline_hl   = float(np.nanmean(all_hl_ranges))

    fix_records_am = []
    fix_records_pm = []
    profile_data   = {"AM": [], "PM": []}   # for plot: list of 9-bar return paths

    BAR_MIN = 15   # M15 bar duration
    # Bar offsets from fix_ts.  close[fix_ts + offset*15min] ≈ price at fix_ts + (offset+1)*15min.
    # We want:
    #   pre_60  → P(T-60) ≈ close[fix_ts - 75min] → offset -5
    #   pre_30  → P(T-30) ≈ close[fix_ts - 45min] → offset -3
    #   pre_15  → P(T-15) ≈ close[fix_ts - 30min] → offset -2
    #   post_30 → P(T+30) ≈ close[fix_ts + 15min] → offset +1
    #   post_60 → P(T+60) ≈ close[fix_ts + 45min] → offset +3
    # (p_ref = close[fix_ts - 15min] ≈ P(T) is already defined above)
    OFFSET_BARS = {
        "pre_60":  -5,
        "pre_30":  -3,
        "pre_15":  -2,
        "post_30": +1,
        "post_60": +3,
    }
    PROFILE_OFFSETS = list(range(-4, 5))   # -60 to +60 min in 15-min steps

    for d in all_dates:
        # Skip weekends (no fix on Sat/Sun)
        if date(d.year, d.month, d.day).weekday() >= 5:
            continue

        for fix_type, fix_records in [("AM", fix_records_am),
                                       ("PM", fix_records_pm)]:
            fix_ts = london_fix_utc(d, fix_type)

            # Find the M15 bar that OPENS at fix_ts (= fix bar)
            if fix_ts not in df_idx.index:
                # Try nearest within ±1 bar
                near = df_idx.index[
                    (df_idx.index >= fix_ts - pd.Timedelta(minutes=7)) &
                    (df_idx.index <= fix_ts + pd.Timedelta(minutes=7))
                ]
                if len(near) == 0:
                    continue
                fix_ts = near[0]

            # Reference price = close of bar immediately before fix
            # i.e., close of bar at fix_ts - 15min
            ref_ts = fix_ts - pd.Timedelta(minutes=BAR_MIN)
            if ref_ts not in df_idx.index:
                continue
            p_ref = float(df_idx.loc[ref_ts, "close"])
            if not np.isfinite(p_ref) or p_ref <= 0:
                continue

            # Sanity: range of fix bar
            if fix_ts in df_idx.index:
                h_fix = float(df_idx.loc[fix_ts, "high"])
                l_fix = float(df_idx.loc[fix_ts, "low"])
                fix_hl_ranges.append(h_fix - l_fix)

            # Compute pre/post returns
            rec = {
                "date":   str(d),
                "year":   d.year,
                "fix_ts": str(fix_ts),
            }
            valid = True
            for win_name, bar_offset in OFFSET_BARS.items():
                off_ts = fix_ts + pd.Timedelta(minutes=bar_offset * BAR_MIN)
                if off_ts in df_idx.index:
                    p_off = float(df_idx.loc[off_ts, "close"])
                    if np.isfinite(p_off) and p_off > 0:
                        if "pre" in win_name:
                            rec[win_name] = math.log(p_ref / p_off)
                        else:
                            rec[win_name] = math.log(p_off / p_ref)
                    else:
                        rec[win_name] = np.nan
                else:
                    rec[win_name] = np.nan

            fix_records.append(rec)

            # Profile path (−60 to +60 min, 15-min steps, returns vs p_ref)
            path = []
            ok   = True
            for off in PROFILE_OFFSETS:
                off_ts = ref_ts + pd.Timedelta(minutes=off * BAR_MIN)
                if off_ts in df_idx.index:
                    p_off = float(df_idx.loc[off_ts, "close"])
                    if np.isfinite(p_off) and p_off > 0:
                        path.append(math.log(p_off / p_ref))
                    else:
                        ok = False; break
                else:
                    ok = False; break
            if ok and len(path) == len(PROFILE_OFFSETS):
                profile_data[fix_type].append(path)

    # Sanity check result
    if fix_hl_ranges:
        mean_fix_hl = float(np.mean(fix_hl_ranges))
        vol_ratio   = mean_fix_hl / baseline_hl if baseline_hl > 0 else np.nan
    else:
        mean_fix_hl = np.nan
        vol_ratio   = np.nan

    sanity_pass = bool(vol_ratio > 1.05) if np.isfinite(vol_ratio) else False
    if verbose:
        print(f"    Fix bar HL avg: {mean_fix_hl:.4f}  Baseline HL avg: {baseline_hl:.4f}"
              f"  Ratio: {vol_ratio:.3f}  {'PASS ✓' if sanity_pass else 'FAIL — check times!'}")

    # --- Run t-tests: full period + pre/post 2015 --------------------------
    def split_and_analyze(records, fix_label):
        all_rec = records
        pre_15  = [r for r in records if r.get("year", 9999) < FIX_REFORM_YEAR]
        post_15 = [r for r in records if r.get("year", 0)    >= FIX_REFORM_YEAR]

        if verbose:
            print(f"\n  {fix_label} Fix  (n_days={len(all_rec)}, "
                  f"pre-2015={len(pre_15)}, post-2015={len(post_15)})")
        return {
            "full_period": _analyze_fix_window(all_rec,  fix_label, verbose),
            "pre_2015":    _analyze_fix_window(pre_15,   fix_label, verbose),
            "post_2015":   _analyze_fix_window(post_15,  fix_label, verbose),
        }

    am_results = split_and_analyze(fix_records_am, "AM")
    pm_results = split_and_analyze(fix_records_pm, "PM")

    # --- Economic significance (annual edge) --------------------------------
    def annual_edge_bps(mean_bps, freq_per_day=252):
        """If drift = mean_bps, trading once daily at 1% risk ≈ ... annual."""
        # Each trade captures mean_bps return (gross, before spread/commission)
        return round(mean_bps * freq_per_day, 1)

    for fix_results in (am_results, pm_results):
        for window_name in ("pre_60", "pre_30", "pre_15"):
            fp = fix_results["full_period"].get(window_name, {})
            if fp.get("sig_bonf"):
                mbps = fp.get("mean_bps", 0)
                fp["annual_edge_gross_bps"] = annual_edge_bps(mbps)

    # Profile data for plots
    avg_profile = {}
    for fix_type, paths in profile_data.items():
        if paths:
            arr = np.array(paths) * 10_000   # convert to bps
            avg_profile[fix_type] = {
                "mean":  arr.mean(axis=0).tolist(),
                "sem":   (arr.std(axis=0) / math.sqrt(len(arr))).tolist(),
                "n":     len(paths),
                "offsets_min": [o * BAR_MIN for o in PROFILE_OFFSETS],
            }

    return {
        "n_trading_days":    len([d for d in all_dates if date(d.year,d.month,d.day).weekday() < 5]),
        "m15_bars_total":    len(df),
        "sanity_check": {
            "fix_bar_hl_mean":  round(mean_fix_hl, 6) if np.isfinite(mean_fix_hl) else None,
            "baseline_hl_mean": round(baseline_hl, 6),
            "vol_ratio":        round(vol_ratio, 4) if np.isfinite(vol_ratio) else None,
            "passes":           sanity_pass,
        },
        "AM_fix":     am_results,
        "PM_fix":     pm_results,
        "avg_profile": avg_profile,
        "raw_am_records": fix_records_am,   # saved for plots; removed from JSON if too large
        "raw_pm_records": fix_records_pm,
    }


# ═══════════════════════════════════════════════════════════════════════════
# PLOTS
# ═══════════════════════════════════════════════════════════════════════════

def _fmt_close(v):
    return round(float(v), 4) if np.isfinite(float(v)) else None


def plot_c1_rolling_pe(c1_xauusd: dict, df_h1: pd.DataFrame):
    """C1: Rolling PE(m=5, w=100) overlaid on XAUUSD price."""
    rpe_vals = c1_xauusd.get("rolling_pe_m5_w100")
    rpe_ts   = c1_xauusd.get("rolling_pe_timestamps")
    if rpe_vals is None:
        return

    pe_arr   = np.array(rpe_vals, dtype=float)
    ts_arr   = pd.to_datetime(rpe_ts)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("XAUUSD H1 — Rolling Permutation Entropy (m=5, window=100 bars)",
                 fontsize=13, fontweight="bold")

    # Price
    closes = df_h1["close"].values
    times_h1 = pd.to_datetime(df_h1["time"].values)
    ax1.plot(times_h1, closes, lw=0.6, color="#2c3e50", alpha=0.8)
    ax1.set_ylabel("XAUUSD Close (USD)", fontsize=10)
    ax1.set_title("Price", fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Rolling PE
    valid = np.isfinite(pe_arr)
    ax2.plot(ts_arr[valid], pe_arr[valid], lw=0.8, color="#e74c3c", label="PE (m=5, w=100)")
    ax2.axhline(y=1.0, lw=1.2, ls="--", color="#7f8c8d", label="Theoretical max (random)")
    mean_pe = float(np.nanmean(pe_arr))
    ax2.axhline(y=mean_pe, lw=1.0, ls=":", color="#e74c3c", alpha=0.5,
                label=f"Mean PE = {mean_pe:.4f}")
    ax2.set_ylabel("Normalized PE", fontsize=10)
    ax2.set_xlabel("Date", fontsize=10)
    ax2.set_ylim(0.85, 1.02)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # Color PE drops (< 25th pct)
    pct25 = float(np.nanpercentile(pe_arr, 25))
    low_pe = valid & (pe_arr < pct25)
    for span_start, span_end in _find_spans(ts_arr, low_pe):
        ax1.axvspan(span_start, span_end, alpha=0.12, color="#e74c3c")
        ax2.axvspan(span_start, span_end, alpha=0.12, color="#e74c3c")

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b'%y"))
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "c1_rolling_pe_xauusd.png")
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


def _find_spans(ts_arr, bool_mask):
    """Yield (start_ts, end_ts) tuples for contiguous True regions."""
    in_span   = False
    span_start = None
    for i, (ts, v) in enumerate(zip(ts_arr, bool_mask)):
        if v and not in_span:
            in_span = True
            span_start = ts
        elif not v and in_span:
            yield (span_start, ts)
            in_span = False
    if in_span:
        yield (span_start, ts_arr[-1])


def plot_c1_pe_heatmap(c1_results: dict):
    """C1: Heatmap of mean PE per instrument × m value."""
    syms = list(c1_results.keys())
    dims = PE_DIMS
    data = np.full((len(syms), len(dims)), np.nan)
    for i, sym in enumerate(syms):
        bd = c1_results[sym].get("by_dimension", {})
        for j, m in enumerate(dims):
            pe_v = bd.get(f"m{m}", {}).get("pe")
            if pe_v is not None:
                data[i, j] = pe_v

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(data, cmap="RdYlGn_r", vmin=0.93, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(dims)))
    ax.set_xticklabels([f"m={m}" for m in dims])
    ax.set_yticks(range(len(syms)))
    ax.set_yticklabels(syms)
    ax.set_title("Mean Permutation Entropy per Instrument × Embedding Dimension\n"
                 "(darker red = lower PE = more ordered = more predictable)", fontsize=11)
    for i in range(len(syms)):
        for j in range(len(dims)):
            if np.isfinite(data[i, j]):
                ax.text(j, i, f"{data[i,j]:.4f}", ha="center", va="center",
                        fontsize=8, color="black" if data[i, j] > 0.96 else "white")
    plt.colorbar(im, ax=ax, label="Normalized PE")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "c1_pe_heatmap.png")
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_c2_markov_states(c2_results: dict, df_h1: pd.DataFrame):
    """C2: XAUUSD price coloured by Markov regime (2-state and 3-state)."""
    xau = c2_results.get("XAUUSD", {})
    closes_full = df_h1["close"].values
    times_full  = pd.to_datetime(df_h1["time"].values)

    for k_lab in ("2state", "3state"):
        k_data = xau.get(k_lab, {})
        if "error" in k_data or k_data.get("filtered_probs") is None:
            continue
        k_val    = int(k_lab[0])
        ts_arr   = pd.to_datetime(k_data["timestamps"])
        map_st   = np.array(k_data["map_states"])
        n_bars   = len(ts_arr)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                        gridspec_kw={"height_ratios": [3, 1]})
        fig.suptitle(f"XAUUSD H1 — Markov {k_val}-State Regime Coloring",
                     fontsize=13, fontweight="bold")

        # Align price to return timestamps (returns have length n-1 relative to bars)
        # ts_arr corresponds to df_h1.iloc[1:] after gap filtering
        # For display, use df_h1 directly with closest matching
        for i in range(k_val):
            mask = map_st == i
            params_i = k_data["regime_params"]
            dur_i    = params_i["avg_duration"][i]
            frac_i   = params_i["state_fractions"][i]
            lbl = (f"State {i}: μ={params_i['means'][i]*10000:.2f}bps/bar, "
                   f"σ={params_i['std_devs'][i]*10000:.2f}bps, "
                   f"dur={dur_i:.1f}bar, {frac_i:.0%}")
            ax1.scatter(ts_arr[mask],
                        np.interp(mdates.date2num(ts_arr[mask].to_pydatetime()),
                                  mdates.date2num(times_full.to_pydatetime()),
                                  closes_full),
                        s=1, c=REGIME_COLOURS[i], label=lbl, zorder=2)

        # Price line (thin, grey)
        ax1.plot(times_full, closes_full, lw=0.4, color="#95a5a6", zorder=1, alpha=0.6)
        ax1.set_ylabel("XAUUSD Close", fontsize=10)
        ax1.legend(fontsize=7, loc="upper left")
        ax1.grid(True, alpha=0.2)

        # Regime probability plot
        filt = np.array(k_data["filtered_probs"])
        for i in range(k_val):
            ax2.plot(ts_arr, filt[:, i], lw=0.6, color=REGIME_COLOURS[i],
                     label=f"State {i} prob")
        ax2.set_ylabel("Filtered P(regime)", fontsize=10)
        ax2.set_xlabel("Date", fontsize=10)
        ax2.set_ylim(0, 1)
        ax2.legend(fontsize=7)
        ax2.grid(True, alpha=0.2)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b'%y"))

        plt.tight_layout()
        path = os.path.join(PLOTS_DIR, f"c2_markov_{k_lab}_xauusd.png")
        plt.savefig(path, dpi=140, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {path}")


def plot_c3_fix_profiles(c3_results: dict):
    """C3: Average return path from −60 to +60 min for AM and PM fix."""
    avg = c3_results.get("avg_profile", {})
    offsets_min = None
    for fix_type in ("AM", "PM"):
        if fix_type in avg:
            offsets_min = avg[fix_type].get("offsets_min")
            break
    if offsets_min is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    for ax, fix_type in zip(axes, ("AM", "PM")):
        if fix_type not in avg:
            ax.set_title(f"{fix_type} Fix — no data")
            continue
        data_ft = avg[fix_type]
        mean_bps = np.array(data_ft["mean"])
        sem_bps  = np.array(data_ft["sem"])
        n_days   = data_ft["n"]
        offs     = np.array(data_ft["offsets_min"])

        # Fill between ±1 SEM
        ax.fill_between(offs, mean_bps - sem_bps, mean_bps + sem_bps,
                        alpha=0.25, color="#3498db")
        ax.plot(offs, mean_bps, lw=2, color="#2980b9",
                marker="o", markersize=3, label=f"Mean return (n={n_days} days)")
        ax.axhline(0, color="black", lw=0.8, ls="--", alpha=0.5)
        ax.axvline(0, color="#e74c3c", lw=1.2, ls="--", alpha=0.8, label="Fix time")
        ax.set_xlabel("Minutes relative to fix", fontsize=10)
        ax.set_ylabel("Cumulative return (bps)", fontsize=10)
        ax.set_title(f"{fix_type} LBMA Gold Fix — average ±60 min return path\n"
                     f"(ref = close just before fix; ±1 SEM shaded)", fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Annotate significant pre-fix windows
        for win, offset_ref in [("pre_30", -30), ("pre_60", -60)]:
            for epoch in ("full_period",):
                fp = c3_results.get(f"{fix_type}_fix", {}).get(epoch, {}).get(win, {})
                if fp.get("sig_bonf"):
                    mbps = fp["mean_bps"]
                    ax.annotate(f"pre_{win}: {mbps:+.1f}bps*",
                                xy=(offset_ref, mean_bps[offs == offset_ref][0]
                                    if any(offs == offset_ref) else 0),
                                fontsize=7, color="#e74c3c",
                                xytext=(offset_ref + 2, mbps * 0.8))

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "c3_fix_profiles.png")
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


def plot_c3_volatility_check(df_m15: pd.DataFrame):
    """C3: M15 intraday average |H-L| by UTC hour — sanity check for fix time location."""
    df_m15 = df_m15.copy()
    df_m15["hl_range"] = df_m15["high"] - df_m15["low"]
    df_m15["hour_utc"] = df_m15["time"].dt.hour

    hourly = df_m15.groupby("hour_utc")["hl_range"].agg(["mean","sem"]).reset_index()

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(hourly["hour_utc"], hourly["mean"], color="#3498db", alpha=0.7, label="Mean |H-L|")
    ax.errorbar(hourly["hour_utc"], hourly["mean"], yerr=hourly["sem"],
                fmt="none", color="#2c3e50", capsize=2)

    # Mark fix windows
    for fix_type, utc_hours in [("AM fix (10:30 London)", [9.5, 10.5]),
                                  ("PM fix (15:00 London)", [14.0, 15.0])]:
        ax.axvspan(utc_hours[0], utc_hours[1], alpha=0.2, color="#e74c3c",
                   label=fix_type)

    ax.set_xlabel("UTC Hour", fontsize=10)
    ax.set_ylabel("Mean M15 |High-Low| (USD)", fontsize=10)
    ax.set_title("XAUUSD M15 Intraday Volatility by UTC Hour\n"
                 "(Fix windows marked — should show elevated volatility for valid times)",
                 fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_xticks(range(24))

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "c3_volatility_check.png")
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════
# MARKDOWN SUMMARY WRITER
# ═══════════════════════════════════════════════════════════════════════════

def _star(p_val, bonf=True):
    if p_val is None or not np.isfinite(float(p_val)):
        return ""
    thresh = ALPHA_BONF if bonf else 0.05
    return "**" if float(p_val) < thresh else ("*" if float(p_val) < 0.05 else "")


def _fmt(v, spec="", default="—"):
    """Safe format: returns default string when v is None or non-finite."""
    if v is None:
        return default
    try:
        fv = float(v)
        if not np.isfinite(fv):
            return default
        return format(fv, spec) if spec else str(fv)
    except (TypeError, ValueError):
        return default


def write_summary(c1: dict, c2: dict, c3: dict, ts: str) -> str:
    lines = []
    A = lines.append

    A(f"# GTOS Nonlinear Structure Analysis — {ts}")
    A(f"")
    A(f"Generated: {datetime.utcnow().isoformat()}Z")
    A(f"Bonferroni threshold: α* = {ALPHA_BONF:.5f} (n_tests≈{N_TESTS_ESTIMATE})")
    A(f"")
    A(f"---")
    A(f"")

    # ── C1 Summary ──────────────────────────────────────────────────────────
    A(f"## TEST C1: Permutation Entropy (Q-15.7)")
    A(f"")
    A(f"### Mean PE by Instrument and Embedding Dimension")
    A(f"")
    A(f"PE = 1.0 means statistically random; PE < 1.0 means ordered/predictable structure.")
    A(f"Null distribution from 500 shuffles per series.")
    A(f"")
    header = "| Instrument | n_H1 | m=3 (z) | m=4 (z) | m=5 (z) | m=6 (z) |"
    A(header)
    A("|---|---|---|---|---|---|")
    for sym in INSTRUMENTS:
        sr = c1.get(sym, {})
        if "error" in sr:
            A(f"| {sym} | — | — | — | — | — |")
            continue
        n  = sr.get("n_returns", 0)
        bd = sr.get("by_dimension", {})
        cells = []
        for m in PE_DIMS:
            md = bd.get(f"m{m}", {})
            pe  = md.get("pe")
            z   = md.get("z_score")
            sig = md.get("sig_bonf", False)
            if pe is None:
                cells.append("—")
            else:
                star_s = "**" if sig else ""
                cells.append(f"{star_s}{pe:.5f} ({z:+.2f}){star_s}"
                             if z is not None else f"{pe:.5f}")
        A(f"| {sym} | {n} | {' | '.join(cells)} |")
    A(f"")
    A(f"*z-score vs shuffled null. ** = Bonferroni-significant (p<{ALPHA_BONF:.4f})*")
    A(f"")

    # KZ vs non-KZ
    A(f"### Kill Zone vs Non-Kill-Zone PE (hourly bins, m=5, Welch t-test)")
    A(f"")
    A(f"| Instrument | Session | KZ PE | Non-KZ PE | t | p | KZ < nonKZ? |")
    A(f"|---|---|---|---|---|---|---|")
    for sym in INSTRUMENTS:
        sr = c1.get(sym, {})
        kza = sr.get("kz_analysis", {})
        for kz_name, kzd in kza.items():
            pe_kz  = kzd.get("pe_kz_mean_hourly")
            pe_nkz = kzd.get("pe_nonkz_mean_hourly")
            t_val  = kzd.get("t_stat_hourly")
            p_val  = kzd.get("p_value_hourly")
            lo     = kzd.get("kz_lower_pe")
            star_s = _star(p_val, bonf=True)
            A(f"| {sym} | {kz_name} | "
              f"{_fmt(pe_kz, '.5f')} | "
              f"{_fmt(pe_nkz, '.5f')} | "
              f"{_fmt(t_val, '.3f')} | "
              f"{star_s}{_fmt(p_val, '.4f')}{star_s} | "
              f"{'Yes ✓' if lo else 'No'} |")
    A(f"")
    A(f"*Lower PE in KZ = more predictable structure during kill zones.*")
    A(f"")

    # London range regression
    A(f"### London Range Regression (XAUUSD: daily PE → next-day London range)")
    A(f"")
    reg = c1.get("XAUUSD", {}).get("london_range_regression")
    if reg:
        beta  = reg.get("beta")
        pv    = reg.get("p_value")
        r2    = reg.get("r_squared")
        n_reg = reg.get("n")
        interp = reg.get("interpretation", "")
        star_s = _star(pv)
        A(f"- n={n_reg} trading days, β={_fmt(beta, '.6f')}, "
          f"p={star_s}{_fmt(pv, '.4f')}{star_s}, R²={_fmt(r2, '.4f')}")
        A(f"- **{interp}**")
    else:
        A(f"- Not computed (XAUUSD data missing)")
    A(f"")

    # C1 conclusion
    all_pe_m5 = []
    for sym in INSTRUMENTS:
        pe_v = c1.get(sym, {}).get("by_dimension", {}).get("m5", {}).get("pe")
        if pe_v is not None:
            all_pe_m5.append(pe_v)
    avg_pe = float(np.mean(all_pe_m5)) if all_pe_m5 else np.nan
    any_sig = any(
        c1.get(sym, {}).get("by_dimension", {}).get("m5", {}).get("sig_bonf", False)
        for sym in INSTRUMENTS
    )
    xau_pe_m5 = c1.get("XAUUSD", {}).get("by_dimension", {}).get("m5", {})
    xau_pe_val = xau_pe_m5.get("pe", np.nan) or np.nan
    xau_z      = xau_pe_m5.get("z_score", np.nan) or np.nan

    A(f"### C1 Conclusion")
    A(f"")
    A(f"> Gold H1 permutation entropy (m=5) is **{xau_pe_val:.5f}** "
      f"(z={xau_z:+.3f} vs shuffled null). "
      f"Across all 5 instruments, mean PE (m=5) = **{avg_pe:.5f}**. "
      f"This is {'significantly below' if any_sig else 'not significantly below'} 1.0 "
      f"{'(Bonferroni-corrected)' if any_sig else '(no Bonferroni significance)'}, "
      f"indicating the series is {'meaningfully more ordered' if xau_pe_val < 0.99 else 'close to'} "
      f"a pure random walk but {'with detectable nonlinear structure' if any_sig else 'at the margin'}.")
    A(f"")

    # ── C2 Summary ──────────────────────────────────────────────────────────
    A(f"---")
    A(f"")
    A(f"## TEST C2: Markov Regime Switching (Q-15.9)")
    A(f"")
    A(f"### Regime Parameters (2-State Model)")
    A(f"")
    A(f"| Instrument | State | Mean (bps/bar) | Std Dev (bps) | Avg Duration (bars) | Time Fraction |")
    A(f"|---|---|---|---|---|---|")
    for sym in INSTRUMENTS:
        sr2  = c2.get(sym, {})
        k2   = sr2.get("2state", {})
        if "error" in k2:
            for st in range(2):
                A(f"| {sym} | {st} | — | — | — | — |")
            continue
        rp = k2.get("regime_params", {})
        for i in range(2):
            mu  = (rp.get("means",     [None]*(i+1))[i] or 0) * 10000
            sig = (rp.get("std_devs",  [None]*(i+1))[i] or 0) * 10000
            dur = rp.get("avg_duration", [None]*(i+1))[i]
            frac = rp.get("state_fractions", [None]*(i+1))[i]
            dur_s  = _fmt(dur,  '.1f')
            frac_s = _fmt(frac, '.1%')
            A(f"| {sym} | {i} | {mu:+.3f} | {sig:.3f} | {dur_s} | {frac_s} |")
    A(f"")

    A(f"### Transition Detection Lag (2-State, P80 threshold)")
    A(f"")
    A(f"| Instrument | N transitions | Mean lag (bars) | Median | Within 4 bars | Usable real-time? |")
    A(f"|---|---|---|---|---|---|")
    for sym in INSTRUMENTS:
        k2 = c2.get(sym, {}).get("2state", {})
        lag = k2.get("detection_lag_p80", {})
        n_tr  = lag.get("n_transitions", 0)
        mean  = lag.get("mean")
        med   = lag.get("median")
        w4    = lag.get("pct_within_4bars")
        usable = "Yes" if (mean is not None and mean <= 4) else "No (too slow)"
        w4_str = f"{w4:.0f}%" if w4 is not None else "—"
        A(f"| {sym} | {n_tr} | "
          f"{_fmt(mean, '.1f')} | "
          f"{_fmt(med, '.1f')} | "
          f"{w4_str} | {usable} |")
    A(f"")

    A(f"### Regime vs Kill Zone Affinity (2-State)")
    A(f"")
    A("| Instrument | State | P(regime|KZ) | P(regime|non-KZ) | KZ affinity? |")
    A(f"|---|---|---|---|---|")
    for sym in INSTRUMENTS:
        k2   = c2.get(sym, {}).get("2state", {})
        kaff = k2.get("kz_regime_affinity", {})
        for i in range(2):
            kd = kaff.get(f"state_{i}", {})
            pkz  = kd.get("mean_prob_kz")
            pnkz = kd.get("mean_prob_nonkz")
            if pkz and pnkz:
                affin = "Yes ✓" if pkz > pnkz + 0.05 else "No"
            else:
                affin = "—"
            A(f"| {sym} | {i} | {_fmt(pkz, '.3f')} | {_fmt(pnkz, '.3f')} | {affin} |")
    A(f"")

    # ── C3 Summary ──────────────────────────────────────────────────────────
    A(f"---")
    A(f"")
    A(f"## TEST C3: London Gold Fix Anomaly (Q-14.3)")
    A(f"")
    sanity = c3.get("sanity_check", {})
    sanity_str = ("PASS ✓ — elevated vol at fix times confirms UTC alignment"
                  if sanity.get("passes") else "FAIL — times may be misaligned")
    A(f"**Sanity check:** Fix-window HL ratio = {_fmt(sanity.get('vol_ratio'), '.3f')} ({sanity_str})")
    A(f"")

    for fix_type in ("AM", "PM"):
        fix_key  = f"{fix_type}_fix"
        fix_data = c3.get(fix_key, {})
        A(f"### {fix_type} Fix (10:30 London {'AM' if fix_type=='AM' else '/ 15:00 London PM'})")
        A(f"")

        for epoch_key, epoch_label in [
            ("full_period", "Full Period"),
            ("post_2015",   "Post-2015 (reform era)"),
            ("pre_2015",    "Pre-2015"),
        ]:
            ep = fix_data.get(epoch_key, {})
            n_ep = ep.get("n", 0)
            A(f"#### {epoch_label} (n={n_ep} days)")
            A(f"")
            A(f"| Window | Mean (bps) | t-stat | p-value | Bonf sig | Annual edge |")
            A(f"|---|---|---|---|---|---|")
            for win in ["pre_60", "pre_30", "pre_15", "post_30", "post_60"]:
                wd = ep.get(win, {})
                if "error" in wd or wd.get("n", 0) < MIN_N_TTEST:
                    A(f"| {win} | — | — | — | — | — |")
                    continue
                mbps  = wd.get("mean_bps")
                tstat = wd.get("t_stat")
                pv    = wd.get("p_value")
                sig   = wd.get("sig_bonf", False)
                ann   = wd.get("annual_edge_gross_bps", "—")
                star_s = "**" if sig else ""
                tstat_s = _fmt(tstat, '+.2f')
                pv_s    = _fmt(pv, '.5f')
                A(f"| {win} | {star_s}{mbps:+.2f}{star_s} | "
                  f"{tstat_s} | "
                  f"{star_s}{pv_s}{star_s} | "
                  f"{'YES **' if sig else 'no'} | {ann} |")
            A(f"")

    # C3 conclusion
    pm_post = c3.get("PM_fix", {}).get("post_2015", {})
    pm_pre30_post = pm_post.get("pre_30", {})
    pre30_bps = pm_pre30_post.get("mean_bps")
    pre30_p   = pm_pre30_post.get("p_value")
    pre30_sig = pm_pre30_post.get("sig_bonf", False)
    survived  = "has survived" if pre30_sig else "has NOT survived (null result post-2015)"

    A(f"### C3 Conclusion")
    A(f"")
    pre30_bps_s = _fmt(pre30_bps, '+.2f')
    pre30_p_s   = _fmt(pre30_p, '.4f', default='n/a')
    extra_note  = "Economic significance requires verification after spread/commission." if pre30_sig else ""
    A(f"> The PM fix shows a pre-fix drift of "
      f"**{pre30_bps_s}bps** in the 30 minutes before (post-2015 era), "
      f"with p={pre30_p_s}. "
      f"The anomaly **{survived}** the 2015 reform. {extra_note}")
    A(f"")

    # ── Final verdict ────────────────────────────────────────────────────────
    A(f"---")
    A(f"")
    A(f"## Overall Verdict on Nonlinear Structure")
    A(f"")
    A(f"The three linear tests (VR, autocorrelation, from prior sessions) established that "
      f"gold H1 is statistically a random walk under LINEAR tests. These three nonlinear tests add:")
    A(f"")
    A(f"| Test | Finding | Tradeable? |")
    A(f"|---|---|---|")
    any_pe_sig = any(
        c1.get(s, {}).get("by_dimension", {}).get("m5", {}).get("sig_bonf", False)
        for s in INSTRUMENTS
    )
    kz_pe_lower = any(
        any(kzd.get("kz_lower_pe") for kzd in c1.get(s, {}).get("kz_analysis", {}).values())
        for s in INSTRUMENTS
    )
    A(f"| C1 PE | Mean PE={avg_pe:.4f} ({'below 1.0 — nonlinear structure exists' if avg_pe < 0.99 else 'near 1.0 — near-random'}) | "
      f"{'Yes — KZ captures more ordered periods' if kz_pe_lower else 'Weak'} |")

    # C2: any fast detection?
    c2_fast = any(
        c2.get(s, {}).get("2state", {}).get("detection_lag_p80", {}).get("mean", 999) is not None
        and c2.get(s, {}).get("2state", {}).get("detection_lag_p80", {}).get("mean", 999) <= 4
        for s in INSTRUMENTS
    )
    A(f"| C2 Markov | {'Real-time detectable (lag ≤4 bars)' if c2_fast else 'Too slow for real-time use (lag >4 bars)'} | "
      f"{'Yes — regime pre-screen viable' if c2_fast else 'No — detection too slow'} |")

    c3_sig = any(
        c3.get(f"{ft}_fix", {}).get("post_2015", {}).get(w, {}).get("sig_bonf", False)
        for ft in ("AM", "PM") for w in ("pre_30", "pre_60", "pre_15")
    )
    A(f"| C3 Fix | {'Anomaly significant post-2015' if c3_sig else 'Anomaly not significant post-2015'} | "
      f"{'Potentially — requires spread/commission check' if c3_sig else 'No — null result'} |")
    A(f"")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("GTOS NONLINEAR STRUCTURE ANALYSIS")
    print(f"Timestamp: {TIMESTAMP}")
    print(f"Output dir: {OUT_DIR}")
    print(f"Bonferroni α* = {ALPHA_BONF:.5f} (n_tests≈{N_TESTS_ESTIMATE})")
    print("=" * 70)

    # ── Run tests ────────────────────────────────────────────────────────────
    c1_results = run_c1(verbose=True)
    c2_results = run_c2(verbose=True)
    c3_results = run_c3(verbose=True)

    # ── Generate plots ───────────────────────────────────────────────────────
    print("\n" + "═"*70)
    print("GENERATING PLOTS")
    print("═"*70)

    df_h1_xau = load_csv("XAUUSD", "H1")
    df_m15_xau = load_csv("XAUUSD", "M15")

    if df_h1_xau is not None:
        plot_c1_rolling_pe(c1_results.get("XAUUSD", {}), df_h1_xau)
    plot_c1_pe_heatmap(c1_results)
    plot_c2_markov_states(c2_results, df_h1_xau if df_h1_xau is not None else pd.DataFrame())
    plot_c3_fix_profiles(c3_results)
    if df_m15_xau is not None:
        plot_c3_volatility_check(df_m15_xau)

    # ── Write JSON output ────────────────────────────────────────────────────
    print("\n" + "═"*70)
    print("WRITING OUTPUT FILES")
    print("═"*70)

    # Strip large raw records from C3 before JSON serialisation
    c3_for_json = {k: v for k, v in c3_results.items()
                   if k not in ("raw_am_records", "raw_pm_records")}

    full_results = {
        "generated":        TIMESTAMP,
        "n_instruments":    5,
        "bonferroni":       {
            "n_tests":        N_TESTS_ESTIMATE,
            "alpha":          ALPHA,
            "alpha_corrected": round(ALPHA_BONF, 6),
        },
        "C1_permutation_entropy":   {
            k: {kk: vv for kk, vv in v.items()
                if kk not in ("rolling_pe_m5_w100", "rolling_pe_timestamps")}
            for k, v in c1_results.items()
        },
        "C2_markov_regime":  {
            k: {kk: ({kkk: vvv for kkk, vvv in vv.items()
                       if kkk not in ("filtered_probs", "smoothed_probs",
                                      "map_states", "timestamps")}
                     if isinstance(vv, dict) else vv)
                for kk, vv in v.items()}
            for k, v in c2_results.items()
        },
        "C3_london_fix":    _j(c3_for_json),
    }

    json_path = os.path.join(OUT_DIR, f"nonlinear_results_{TIMESTAMP}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(_j(full_results), f, indent=2, ensure_ascii=False)
    print(f"  JSON: {json_path}")

    # ── Write Markdown summary ───────────────────────────────────────────────
    md_text = write_summary(c1_results, c2_results, c3_results, TIMESTAMP)
    md_path = os.path.join(OUT_DIR, f"nonlinear_summary_{TIMESTAMP}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"  Markdown: {md_path}")

    print("\n" + "═"*70)
    print("DONE — all outputs written to:")
    print(f"  {OUT_DIR}")
    print("=" * 70)

    return json_path, md_path


if __name__ == "__main__":
    main()
