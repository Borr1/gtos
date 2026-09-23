#!/usr/bin/env python3
"""
GTOS Distributional Characterization Analysis
==============================================
Complete statistical characterization of return distributions for all 5 GTOS instruments
at H1, M15, and D1 timeframes.  Every property deviating from a Gaussian random walk is
catalogued as a potential tradeable edge, with statistical AND economic significance evaluated.

Analyses run (per instrument × timeframe × session):
  a) Moments: mean, std, skewness, excess kurtosis — bootstrap 95% CIs
  b) Normality: Jarque-Bera, Shapiro-Wilk, Anderson-Darling, Kolmogorov-Smirnov
  c) Tails: GPD/POT fit, tail index, 1%/0.5%/0.1% quantiles, sigma-event counts
  d) Autocorrelation: ACF of returns/|returns|/returns², Ljung-Box at lags 5/10/20
  e) Volatility clustering: GARCH(1,1), EGARCH(1,1,1) — persistence, half-life, leverage
  f) Jumps: rolling-MAD jump detector, post-jump return forecasts (lags 1/2/4), hourly clustering
  g) Intraday seasonality: hourly mean/vol, Kruskal-Wallis
  h) Conditional distributions: by prev-return sign, by ATR regime, by session position

Outputs:
    research/diagnostics/distributional_characterization_<ts>.json
    research/diagnostics/distributional_summary_<ts>.md
    research/diagnostics/plots/dist_*.png

Usage:
    python research/diagnostics/run_distributional_analysis.py

Notes:
    - Uses same CSV files as run_variance_ratio.py (data/historical/<prefix>_<TF>.csv)
    - If MT5 not available, script uses existing CSVs only — no live data pull
    - GARCH skipped for D1 (n < 500 threshold) and when arch convergence fails
    - Bonferroni correction applied across full test matrix (~540 tests → α* ≈ 0.00009)
"""

import os
import sys
import json
import warnings
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import jarque_bera, anderson, kstest, shapiro, genpareto, skew, kurtosis

try:
    from statsmodels.tsa.stattools import acf
    from statsmodels.stats.diagnostic import acorr_ljungbox
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("WARNING: statsmodels not found.  ACF/LjungBox will use manual fallback.")

try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False
    print("WARNING: arch not found.  GARCH/EGARCH analysis will be skipped.")
    print("Install: pip install arch")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

REPO_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR   = os.path.join(REPO_ROOT, "data", "historical")
OUT_DIR    = os.path.dirname(__file__)
PLOTS_DIR  = os.path.join(OUT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

TIMESTAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

# Instrument definitions
INSTRUMENTS = {
    "XAUUSD": {"prefix": "XAUUSD",    "tfs": ["M15", "H1", "D1"]},
    "US30":   {"prefix": "US30_cash", "tfs": ["M15", "H1", "D1"]},
    "USDJPY": {"prefix": "USDJPY",    "tfs": ["M15", "H1", "D1"]},
    "GBPJPY": {"prefix": "GBPJPY",    "tfs": ["M15", "H1", "D1"]},
    "GBPUSD": {"prefix": "GBPUSD",    "tfs": ["M15", "H1", "D1"]},
}

# UTC kill zone hours (half-open intervals [lo, hi) )
KILL_ZONES = {
    "XAUUSD": {"London": (7.0, 10.5), "NY": (13.0, 17.0)},
    "US30":   {"London": (8.0, 10.5), "NY": (13.5, 16.0)},
    "USDJPY": {"London": (7.0, 9.5),  "NY": (13.0, 15.5)},
    "GBPJPY": {"London": (7.0, 9.5),  "NY": (13.0, 15.5)},
    "GBPUSD": {"London": (7.0, 12.0), "NY": (13.0, 15.5)},
}

# Session open hours (first H1 bar of a session, UTC)
SESSION_OPEN_HOURS = {
    "XAUUSD": {"london": 7, "ny": 13},
    "US30":   {"london": 8, "ny": 14},
    "USDJPY": {"london": 7, "ny": 13},
    "GBPJPY": {"london": 7, "ny": 13},
    "GBPUSD": {"london": 7, "ny": 13},
}

# Bar durations in minutes
TF_MINUTES = {"M15": 15, "H1": 60, "D1": 1440}

# Annual bar counts (24/5 FX, 260 trading days)
BARS_PER_YEAR = {"M15": 24_960, "H1": 6_240, "D1": 261}

# Transaction cost estimates (round-trip, basis points, 1 bp = 0.01%)
TX_COST_BPS = {
    "XAUUSD": 4, "US30": 8, "USDJPY": 2.5, "GBPJPY": 3.5, "GBPUSD": 2.5
}

# Bootstrap configuration
N_BOOT     = 1000     # bootstrap resamples
MAX_BOOT_N = 8_000    # subsample cap for bootstrap (speed)

# Minimum observations thresholds
MIN_OBS_BASIC   = 50    # for any analysis at all
MIN_OBS_GARCH   = 300   # for GARCH fitting
MIN_OBS_GPD     = 25    # minimum exceedances for GPD fit
MIN_OBS_SW      = 30    # Shapiro-Wilk minimum
MAX_OBS_SW      = 5_000 # Shapiro-Wilk maximum (scipy limitation)

# Jump detection
JUMP_SIGMA_THRESHOLD = 4.0   # z-score threshold — rolling-std self-adjusts; max|z| typically ~4.5-5 for fat-tailed assets
JUMP_WINDOW = {"M15": 96, "H1": 24, "D1": 5}   # rolling vol window

# GPD threshold percentile
GPD_THRESHOLD_PCT = 0.90

# Number of tests for Bonferroni correction
# 5 instruments × 3 TF × 3 sessions × ~12 hypothesis tests ≈ 540
N_TOTAL_TESTS = 540
BONFERRONI_ALPHA = 0.05 / N_TOTAL_TESTS   # ≈ 0.000093

print(f"Bonferroni-corrected α* = {BONFERRONI_ALPHA:.6f}  ({N_TOTAL_TESTS} total tests)")


# ═══════════════════════════════════════════════════════════════════════════════
# JSON SERIALISATION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

class _NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):   return int(obj)
        if isinstance(obj, (np.floating,)):  return float(obj)
        if isinstance(obj, np.ndarray):      return obj.tolist()
        if isinstance(obj, pd.Timestamp):    return str(obj)
        return super().default(obj)

def _safe(x):
    """Convert to a JSON-safe Python scalar."""
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    if isinstance(x, (np.integer,)):   return int(x)
    if isinstance(x, (np.floating,)):  return float(x)
    return x


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_ohlcv(symbol: str, tf: str) -> Optional[pd.DataFrame]:
    """Load OHLCV DataFrame (columns: time, open, high, low, close) or None."""
    prefix = INSTRUMENTS[symbol]["prefix"]
    path   = os.path.join(DATA_DIR, f"{prefix}_{tf}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])
    df["time"]  = pd.to_datetime(df["time"])
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)
    return df


def compute_log_returns(df: pd.DataFrame, tf: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute log returns, discarding returns that span overnight/weekend gaps.
    Returns (r, t) where t is the timestamp of the *closing* bar.
    """
    closes = df["close"].values.astype(np.float64)
    times  = df["time"].values

    r = np.diff(np.log(closes))
    t = times[1:]

    if tf == "D1":
        valid = np.isfinite(r)
    else:
        expected_min  = TF_MINUTES[tf]
        gaps_min      = df["time"].diff().dt.total_seconds().iloc[1:].values / 60
        valid         = (gaps_min <= expected_min * 3) & np.isfinite(r)

    return r[valid], t[valid]


def filter_session(r: np.ndarray, t: np.ndarray,
                   symbol: str, session: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filter returns to a named session ('All', 'London', 'NY').
    Session hours are per-instrument kill zone windows.
    """
    if session == "All" or t is None:
        return r, t

    kz = KILL_ZONES.get(symbol, {})
    if session not in kz:
        return r, t

    lo, hi = kz[session]
    dt   = pd.DatetimeIndex(t)
    frac = dt.hour + dt.minute / 60.0
    mask = (frac >= lo) & (frac < hi)
    return r[mask], t[mask]


def compute_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Compute Average True Range from OHLCV dataframe."""
    if not all(c in df.columns for c in ["high", "low", "close"]):
        return np.full(len(df), np.nan)
    high  = df["high"].values.astype(np.float64)
    low   = df["low"].values.astype(np.float64)
    close = df["close"].values.astype(np.float64)
    prev  = np.roll(close, 1); prev[0] = close[0]
    tr = np.maximum(np.maximum(high - low, np.abs(high - prev)), np.abs(low - prev))
    atr = pd.Series(tr).rolling(period, min_periods=1).mean().values
    return atr


# ═══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def bootstrap_moments(r: np.ndarray, n_boot: int = N_BOOT,
                      max_n: int = MAX_BOOT_N) -> Dict:
    """
    Bootstrap CI for mean, std, skewness, excess kurtosis simultaneously.
    Uses vectorised numpy operations.
    """
    n = len(r)
    bn = min(n, max_n)
    if bn < n:
        rng_idx = np.random.choice(n, bn, replace=False)
        r_boot  = r[rng_idx]
    else:
        r_boot  = r

    # Shape: (n_boot, bn) — each row is one resample
    idx  = np.random.randint(0, bn, size=(n_boot, bn))
    samp = r_boot[idx]

    b_means = samp.mean(axis=1)
    b_stds  = samp.std(axis=1, ddof=1)
    b_skews = stats.skew(samp, axis=1)
    b_kurts = stats.kurtosis(samp, axis=1)   # excess kurtosis (Fisher)

    def ci(arr):
        return [_safe(float(np.percentile(arr, 2.5))),
                _safe(float(np.percentile(arr, 97.5)))]

    return {
        "mean_ci95":           ci(b_means),
        "std_ci95":            ci(b_stds),
        "skewness_ci95":       ci(b_skews),
        "excess_kurtosis_ci95":ci(b_kurts),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# A) MOMENTS ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_moments(r: np.ndarray, tf: str) -> Dict:
    n = len(r)
    if n < MIN_OBS_BASIC:
        return {"status": "insufficient_data", "n": n}

    nbpy = BARS_PER_YEAR[tf]
    mu   = float(np.mean(r))
    sig  = float(np.std(r, ddof=1))
    sk   = float(stats.skew(r))
    ku   = float(stats.kurtosis(r))   # excess kurtosis

    ci = bootstrap_moments(r)

    return {
        "n": n,
        "mean_per_period":    _safe(mu),
        "mean_annualized":    _safe(mu * nbpy),
        "mean_ci95":          ci["mean_ci95"],
        "std_per_period":     _safe(sig),
        "std_annualized":     _safe(sig * np.sqrt(nbpy)),
        "std_ci95":           ci["std_ci95"],
        "skewness":           _safe(sk),
        "skewness_ci95":      ci["skewness_ci95"],
        "excess_kurtosis":    _safe(ku),
        "excess_kurtosis_ci95": ci["excess_kurtosis_ci95"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# B) NORMALITY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_normality(r: np.ndarray) -> Dict:
    n = len(r)
    if n < MIN_OBS_BASIC:
        return {"status": "insufficient_data", "n": n}

    result = {"n": n}

    # 1. Jarque-Bera
    try:
        jb_s, jb_p = jarque_bera(r)
        result["jarque_bera"] = {
            "statistic": _safe(jb_s), "p_value": _safe(jb_p),
            "reject_p05": bool(jb_p < 0.05),
            "reject_bonferroni": bool(jb_p < BONFERRONI_ALPHA),
            "note": "Tests skewness + kurtosis jointly"
        }
    except Exception as e:
        result["jarque_bera"] = {"error": str(e)}

    # 2. Shapiro-Wilk (subsample if needed)
    try:
        sw_n   = min(n, MAX_OBS_SW)
        sw_dat = r if sw_n == n else np.random.choice(r, sw_n, replace=False)
        if len(sw_dat) >= MIN_OBS_SW:
            sw_s, sw_p = shapiro(sw_dat)
            result["shapiro_wilk"] = {
                "n_used": sw_n, "statistic": _safe(sw_s), "p_value": _safe(sw_p),
                "reject_p05": bool(sw_p < 0.05),
                "reject_bonferroni": bool(sw_p < BONFERRONI_ALPHA),
                "note": "Reliable for n<=5000; subsampled if larger"
            }
        else:
            result["shapiro_wilk"] = {"status": "too_few_obs"}
    except Exception as e:
        result["shapiro_wilk"] = {"error": str(e)}

    # 3. Anderson-Darling
    try:
        ad = anderson(r, dist="norm")
        # significance_level order: [15, 10, 5, 2.5, 1] percent
        result["anderson_darling"] = {
            "statistic": _safe(ad.statistic),
            "critical_values": [_safe(v) for v in ad.critical_values],
            "significance_levels": list(ad.significance_level),
            "reject_at_5pct": bool(ad.statistic > ad.critical_values[2]),
            "reject_at_1pct": bool(ad.statistic > ad.critical_values[4]),
            "note": "More sensitive in tails than JB"
        }
    except Exception as e:
        result["anderson_darling"] = {"error": str(e)}

    # 4. KS test against fitted normal
    try:
        r_std  = (r - r.mean()) / r.std()
        ks_s, ks_p = kstest(r_std, "norm")
        result["kolmogorov_smirnov"] = {
            "statistic": _safe(ks_s), "p_value": _safe(ks_p),
            "reject_p05": bool(ks_p < 0.05),
            "reject_bonferroni": bool(ks_p < BONFERRONI_ALPHA),
            "note": "KS against N(mu, sigma) fitted to data"
        }
    except Exception as e:
        result["kolmogorov_smirnov"] = {"error": str(e)}

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# C) TAIL ANALYSIS  (GPD / Peaks-over-Threshold)
# ═══════════════════════════════════════════════════════════════════════════════

def _pot_quantile(q_exceedance, threshold, xi, sigma, n, n_exc):
    """
    Return the level x such that P(X > x) = q_exceedance, using POT formula.
    q_exceedance = exceedance probability (e.g. 0.01 for 99th pct).
    """
    ratio = q_exceedance * n / n_exc
    if abs(xi) < 1e-8:
        return threshold + sigma * np.log(1.0 / ratio)
    else:
        return threshold + sigma / xi * (ratio ** (-xi) - 1.0)


def analyze_tails(r: np.ndarray, tf: str) -> Dict:
    n = len(r)
    if n < MIN_OBS_BASIC:
        return {"status": "insufficient_data"}

    nbpy = BARS_PER_YEAR[tf]
    mu   = r.mean()
    sig  = r.std()
    result = {}

    # ── sigma-event counts ───────────────────────────────────────────────────
    for k in [3, 4]:
        empirical  = float(np.sum(np.abs(r) > k * sig) / n * nbpy)
        gaussian   = float(2 * (1 - stats.norm.cdf(k)) * nbpy)
        result[f"sigma{k}_events_per_year_empirical"] = _safe(empirical)
        result[f"sigma{k}_events_per_year_gaussian"]  = _safe(gaussian)
        result[f"sigma{k}_excess_ratio"]              = _safe(empirical / max(gaussian, 0.001))

    # ── GPD fitting ──────────────────────────────────────────────────────────
    for tail_name, tail_r in [("upper", r), ("lower", -r)]:
        u = float(np.percentile(tail_r, GPD_THRESHOLD_PCT * 100))
        exc = tail_r[tail_r > u] - u
        n_exc = len(exc)

        if n_exc < MIN_OBS_GPD:
            result[tail_name] = {"status": f"too_few_exceedances ({n_exc} < {MIN_OBS_GPD})"}
            continue

        try:
            xi, _loc, sigma = genpareto.fit(exc, floc=0)

            q01  = _safe(_pot_quantile(0.01,  u, xi, sigma, n, n_exc))
            q005 = _safe(_pot_quantile(0.005, u, xi, sigma, n, n_exc))
            q001 = _safe(_pot_quantile(0.001, u, xi, sigma, n, n_exc))

            if xi > 0.1:   interp = "PARETO (fat-tailed, power-law decay)"
            elif xi < -0.1: interp = "BOUNDED (thin-tailed, finite maximum)"
            else:           interp = "EXPONENTIAL (near-Gaussian tail)"

            result[tail_name] = {
                "threshold_u":       _safe(u),
                "n_exceedances":     int(n_exc),
                "pct_exceedances":   _safe(n_exc / n),
                "gpd_shape_xi":      _safe(float(xi)),
                "gpd_scale_sigma":   _safe(float(sigma)),
                "infinite_variance": bool(xi >= 0.5),
                "infinite_mean":     bool(xi >= 1.0),
                "q_1pct":   q01,
                "q_0.5pct": q005,
                "q_0.1pct": q001,
                "tail_interpretation": interp,
            }
        except Exception as e:
            result[tail_name] = {"error": str(e)}

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# D) AUTOCORRELATION (returns, |returns|, squared returns)
# ═══════════════════════════════════════════════════════════════════════════════

def _manual_acf(r: np.ndarray, nlags: int = 20):
    """Fallback ACF without statsmodels."""
    n  = len(r)
    mu = r.mean()
    v  = np.dot(r - mu, r - mu) / n
    acf_vals = []
    for k in range(1, nlags + 1):
        cov = np.mean((r[:-k] - mu) * (r[k:] - mu))
        acf_vals.append(cov / v if v > 0 else 0.0)
    return np.array(acf_vals)


def analyze_acf(r: np.ndarray) -> Dict:
    n = len(r)
    if n < MIN_OBS_BASIC:
        return {"status": "insufficient_data"}

    bartlett_ci = 1.96 / np.sqrt(n)
    result = {"bartlett_ci_95": _safe(bartlett_ci)}

    series_map = {
        "returns":         r,
        "abs_returns":     np.abs(r),
        "squared_returns": r ** 2,
    }

    for s_name, s in series_map.items():
        try:
            if HAS_STATSMODELS:
                acf_vals, confint = acf(s, nlags=20, alpha=0.05, fft=True)
                lags = [_safe(float(v)) for v in acf_vals[1:21]]
                lb = acorr_ljungbox(s, lags=[5, 10, 20], return_df=True)
                lb_result = {
                    "lag5":  {"statistic": _safe(float(lb["lb_stat"].iloc[0])),
                              "p_value":   _safe(float(lb["lb_pvalue"].iloc[0]))},
                    "lag10": {"statistic": _safe(float(lb["lb_stat"].iloc[1])),
                              "p_value":   _safe(float(lb["lb_pvalue"].iloc[1]))},
                    "lag20": {"statistic": _safe(float(lb["lb_stat"].iloc[2])),
                              "p_value":   _safe(float(lb["lb_pvalue"].iloc[2]))},
                }
            else:
                lags = [_safe(float(v)) for v in _manual_acf(s, 20)]
                lb_result = None

            sig_lags = [i + 1 for i, v in enumerate(lags)
                        if v is not None and abs(v) > bartlett_ci]

            result[s_name] = {
                "acf_lags_1_20":   lags,
                "significant_lags": sig_lags,
                "max_acf":          _safe(max((abs(v) for v in lags if v is not None), default=0.0)),
                "ljung_box":        lb_result,
            }
        except Exception as e:
            result[s_name] = {"error": str(e)}

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# E) GARCH / EGARCH
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_garch(r: np.ndarray) -> Dict:
    if not HAS_ARCH:
        return {"status": "arch_not_installed"}
    n = len(r)
    if n < MIN_OBS_GARCH:
        return {"status": f"insufficient_data ({n} < {MIN_OBS_GARCH})"}

    result = {}
    r_pct  = r * 100.0   # scale for numerical stability

    # ── GARCH(1,1) ───────────────────────────────────────────────────────────
    try:
        am  = arch_model(r_pct, vol="GARCH", p=1, q=1, dist="Normal", rescale=False)
        res = am.fit(disp="off", show_warning=False, options={"maxiter": 2000})

        p    = res.params
        omega_v = float(p.get("omega",    p.iloc[1] if len(p) > 1 else np.nan))
        alpha_v = float(p.get("alpha[1]", p.iloc[2] if len(p) > 2 else np.nan))
        beta_v  = float(p.get("beta[1]",  p.iloc[3] if len(p) > 3 else np.nan))
        persist = alpha_v + beta_v

        if persist < 1.0 and persist > 0:
            half_life = float(np.log(0.5) / np.log(persist))
        else:
            half_life = None   # non-stationary or edge case

        result["garch11"] = {
            "omega":            _safe(omega_v),
            "alpha_arch":       _safe(alpha_v),
            "beta_garch":       _safe(beta_v),
            "persistence":      _safe(persist),
            "half_life_periods":_safe(half_life),
            "converged":        bool(res.convergence_flag == 0),
            "log_likelihood":   _safe(float(res.loglikelihood)),
            "interpretation": (
                "HIGHLY PERSISTENT (vol clusters strongly)" if persist > 0.95 else
                "PERSISTENT (moderate clustering)"          if persist > 0.85 else
                "MODERATE clustering"
            ),
        }
    except Exception as e:
        result["garch11"] = {"error": str(e)}

    # ── EGARCH(1,1,1) ────────────────────────────────────────────────────────
    try:
        am_e  = arch_model(r_pct, vol="EGARCH", p=1, q=1, o=1, dist="Normal", rescale=False)
        res_e = am_e.fit(disp="off", show_warning=False, options={"maxiter": 2000})

        pe = res_e.params
        result["egarch"] = {
            "omega":        _safe(float(pe.get("omega",    np.nan))),
            "alpha":        _safe(float(pe.get("alpha[1]", np.nan))),
            "gamma":        _safe(float(pe.get("gamma[1]", np.nan))),
            "beta":         _safe(float(pe.get("beta[1]",  np.nan))),
            "leverage_effect_present": (
                float(pe.get("gamma[1]", 0)) < -0.02  if "gamma[1]" in pe.index else None
            ),
            "converged":    bool(res_e.convergence_flag == 0),
            "log_likelihood": _safe(float(res_e.loglikelihood)),
            "note": "gamma<0 = negative shocks increase vol more than positive shocks",
        }
    except Exception as e:
        result["egarch"] = {"error": str(e)}

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# F) JUMP DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_jumps(r: np.ndarray, t: np.ndarray, tf: str) -> Dict:
    n = len(r)
    if n < 100:
        return {"status": "insufficient_data"}

    nbpy = BARS_PER_YEAR[tf]
    K    = JUMP_WINDOW.get(tf, 24)

    # Vectorised rolling std with pandas (efficient)
    r_s   = pd.Series(r)
    roll_std = r_s.rolling(K, min_periods=max(K // 4, 5)).std().values.copy()
    roll_std[roll_std == 0] = np.nan
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(np.isfinite(roll_std) & (roll_std > 0), r / roll_std, np.nan)

    jump_mask = np.abs(z) > JUMP_SIGMA_THRESHOLD
    jump_mask = jump_mask & np.isfinite(z)
    jump_idx  = np.where(jump_mask)[0]
    n_jumps   = int(np.sum(jump_mask))

    if n_jumps == 0:
        return {
            "threshold_sigma": JUMP_SIGMA_THRESHOLD,
            "n_jumps": 0,
            "jump_frequency_per_day": 0.0,
        }

    jumps_per_day = float(n_jumps / n * (nbpy / 260.0))

    # ── Post-jump return analysis ─────────────────────────────────────────────
    post_jump = {}
    for lag in [1, 2, 4]:
        valid_jidx = jump_idx[jump_idx + lag < n]
        if len(valid_jidx) < 5:
            continue
        # Direction-adjusted post-jump return: continuation = positive
        post = r[valid_jidx + lag] * np.sign(r[valid_jidx])
        t_res = stats.ttest_1samp(post, 0)
        post_jump[f"lag_{lag}"] = {
            "n":         int(len(post)),
            "mean":      _safe(float(post.mean())),
            "std":       _safe(float(post.std())),
            "t_stat":    _safe(float(t_res.statistic)),
            "p_value":   _safe(float(t_res.pvalue)),
            "pct_continuation": _safe(float(np.mean(post > 0))),
            "interpretation": "CONTINUATION" if post.mean() > 0 else "REVERSION",
        }

    # ── Hourly clustering ─────────────────────────────────────────────────────
    hourly_rate = {}
    try:
        dt_all   = pd.DatetimeIndex(t)
        dt_jumps = pd.DatetimeIndex(t[jump_mask])
        for h in range(24):
            n_bars_h  = int((dt_all.hour == h).sum())
            n_jumps_h = int((dt_jumps.hour == h).sum())
            if n_bars_h > 0:
                hourly_rate[h] = _safe(float(n_jumps_h / n_bars_h))
        peak_hour = max(hourly_rate, key=hourly_rate.get) if hourly_rate else None
    except Exception:
        peak_hour = None

    return {
        "threshold_sigma":       JUMP_SIGMA_THRESHOLD,
        "n_jumps":               n_jumps,
        "jump_frequency_per_day":_safe(jumps_per_day),
        "avg_jump_z_score":      _safe(float(np.mean(np.abs(z[jump_mask])))),
        "avg_jump_return_abs":   _safe(float(np.mean(np.abs(r[jump_mask])))),
        "post_jump_returns":     post_jump,
        "hourly_jump_rate":      hourly_rate,
        "peak_jump_hour_utc":    peak_hour,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# G) INTRADAY SEASONALITY
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_intraday(r: np.ndarray, t: np.ndarray) -> Dict:
    if t is None or len(r) < MIN_OBS_BASIC:
        return {"status": "insufficient_data"}
    try:
        dt = pd.DatetimeIndex(t)
        df = pd.DataFrame({"r": r, "hour": dt.hour})

        hourly = df.groupby("hour")["r"].agg(
            n="count",
            mean="mean",
            std="std",
            mean_abs=lambda x: np.mean(np.abs(x))
        ).reset_index()

        # Kruskal-Wallis across hours (test: does hour affect return distribution?)
        groups = [grp["r"].values for _, grp in df.groupby("hour") if len(grp) >= 10]
        if len(groups) >= 3:
            kw_stat, kw_p = stats.kruskal(*groups)
        else:
            kw_stat, kw_p = np.nan, np.nan

        # Peak volatility hour
        if len(hourly) > 0:
            peak_vol_hour = int(hourly.loc[hourly["mean_abs"].idxmax(), "hour"])
        else:
            peak_vol_hour = None

        return {
            "kruskal_wallis_statistic": _safe(kw_stat),
            "kruskal_wallis_p_value":   _safe(kw_p),
            "kw_significant_p05":       bool(kw_p < 0.05),
            "peak_abs_return_hour_utc": peak_vol_hour,
            "by_hour": {
                int(row["hour"]): {
                    "n":        int(row["n"]),
                    "mean_r":   _safe(float(row["mean"])),
                    "std_r":    _safe(float(row["std"])) if pd.notna(row["std"]) else None,
                    "mean_abs_r": _safe(float(row["mean_abs"])),
                }
                for _, row in hourly.iterrows()
            },
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# H) CONDITIONAL DISTRIBUTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _compare_groups(g1: np.ndarray, g2: np.ndarray,
                    label1: str, label2: str) -> Dict:
    """Welch t-test + descriptive stats for two groups."""
    if len(g1) < 10 or len(g2) < 10:
        return {"status": "too_few_obs"}
    t_stat, t_p = stats.ttest_ind(g1, g2, equal_var=False)
    return {
        "group1_label":  label1,
        "group1_n":      int(len(g1)),
        "group1_mean":   _safe(float(g1.mean())),
        "group1_std":    _safe(float(g1.std())),
        "group2_label":  label2,
        "group2_n":      int(len(g2)),
        "group2_mean":   _safe(float(g2.mean())),
        "group2_std":    _safe(float(g2.std())),
        "mean_diff":     _safe(float(g1.mean() - g2.mean())),
        "t_statistic":   _safe(float(t_stat)),
        "p_value":       _safe(float(t_p)),
        "significant_p05": bool(t_p < 0.05),
        "significant_bonferroni": bool(t_p < BONFERRONI_ALPHA),
    }


def analyze_conditional(r: np.ndarray, t: np.ndarray,
                        df_full: pd.DataFrame, symbol: str, tf: str) -> Dict:
    n = len(r)
    if n < 60:
        return {"status": "insufficient_data"}

    result = {}

    # 1. By sign of previous return
    try:
        prev_r   = r[:-1]
        curr_r   = r[1:]
        pos_prev = curr_r[prev_r > 0]
        neg_prev = curr_r[prev_r < 0]
        result["by_prev_return_sign"] = _compare_groups(
            pos_prev, neg_prev, "prev_positive", "prev_negative"
        )
        # Asymmetric autocorrelation: do up moves predict up or down?
        result["lag1_autocorrelation_positive_only"] = _safe(
            float(np.corrcoef(prev_r[prev_r > 0], curr_r[prev_r > 0])[0, 1])
            if len(pos_prev) > 10 else None
        )
    except Exception as e:
        result["by_prev_return_sign"] = {"error": str(e)}

    # 2. By ATR regime (high vs low volatility environment)
    try:
        atr = compute_atr(df_full)
        # Align ATR with returns: ATR at bar i corresponds to return r_i = log(close[i]/close[i-1])
        # We need ATR for the "previous bar" to avoid look-ahead
        atr_prev = atr[:-1]   # ATR at the bar *before* the return
        r_curr   = r
        if len(atr_prev) == len(r_curr):
            valid    = np.isfinite(atr_prev) & (atr_prev > 0)
            atr_filt = atr_prev[valid]
            r_filt   = r_curr[valid]
            med_atr  = np.median(atr_filt)
            r_hi_atr = r_filt[atr_filt > med_atr]
            r_lo_atr = r_filt[atr_filt <= med_atr]
            result["by_atr_regime"] = _compare_groups(
                r_hi_atr, r_lo_atr, "high_ATR_prev", "low_ATR_prev"
            )
            result["by_atr_regime"]["median_atr"] = _safe(float(med_atr))
    except Exception as e:
        result["by_atr_regime"] = {"error": str(e)}

    # 3. By session position (session-open bar vs mid-session)
    try:
        if t is not None:
            dt       = pd.DatetimeIndex(t)
            open_hrs = SESSION_OPEN_HOURS.get(symbol, {})
            if open_hrs:
                open_mask = np.isin(dt.hour, list(open_hrs.values()))
                r_open    = r[open_mask]
                r_mid     = r[~open_mask]
                result["by_session_position"] = _compare_groups(
                    r_open, r_mid, "session_open_bar", "mid_session_bar"
                )
    except Exception as e:
        result["by_session_position"] = {"error": str(e)}

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# I) YEAR-BY-YEAR STABILITY CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_stability(r: np.ndarray, t: np.ndarray) -> Dict:
    """Report moments per calendar year to assess distributional stability."""
    if t is None or len(r) < MIN_OBS_BASIC:
        return {"status": "insufficient_data"}
    try:
        dt = pd.DatetimeIndex(t)
        df = pd.DataFrame({"r": r, "year": dt.year})
        out = {}
        for year, grp in df.groupby("year"):
            rv = grp["r"].values
            if len(rv) < 30:
                continue
            out[int(year)] = {
                "n":               int(len(rv)),
                "mean_per_period": _safe(float(rv.mean())),
                "std_per_period":  _safe(float(rv.std(ddof=1))),
                "skewness":        _safe(float(stats.skew(rv))),
                "excess_kurtosis": _safe(float(stats.kurtosis(rv))),
            }
        return out
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PLOTTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _savefig(fig, name: str):
    path = os.path.join(PLOTS_DIR, f"dist_{name}.png")
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_qq(r: np.ndarray, symbol: str, tf: str, session: str) -> str:
    """Q-Q plot: empirical quantiles vs theoretical normal."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"Q-Q Plot  |  {symbol} {tf}  ({session})", fontsize=13, fontweight="bold")

    # Standardize
    r_std = (r - r.mean()) / r.std()

    # Left: Q-Q versus normal
    from scipy.stats import probplot
    ax = axes[0]
    (quantiles, values), (slope, intercept, r_val) = probplot(r_std, dist="norm")
    ax.scatter(quantiles, values, alpha=0.25, s=2, color="#2196F3", rasterized=True)
    lim = max(abs(np.min(quantiles)), abs(np.max(quantiles))) * 1.1
    ax.plot([-lim, lim], [-lim * slope + intercept, lim * slope + intercept],
            "r-", linewidth=1.5, label=f"Normal fit (r={r_val:.4f})")
    ax.set_xlabel("Theoretical Quantiles (Normal)")
    ax.set_ylabel("Sample Quantiles")
    ax.set_title("Q-Q vs Normal")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Right: histogram with kernel density + normal fit
    ax2 = axes[1]
    bins = min(80, max(30, len(r) // 100))
    ax2.hist(r_std, bins=bins, density=True, alpha=0.5, color="#90CAF9", edgecolor="none",
             label="Empirical")
    x_range = np.linspace(r_std.min(), r_std.max(), 300)
    ax2.plot(x_range, stats.norm.pdf(x_range), "r-", linewidth=2, label="Normal(0,1)")
    ax2.set_xlabel("Standardised Return")
    ax2.set_ylabel("Density")
    ax2.set_title(f"Distribution  (skew={stats.skew(r_std):.3f}, kurt={stats.kurtosis(r_std):.3f})")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return _savefig(fig, f"qq_{symbol}_{tf}_{session}")


def plot_acf_panel(r: np.ndarray, symbol: str, tf: str, session: str) -> str:
    """Three-panel ACF: returns, |returns|, squared returns."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    fig.suptitle(f"Autocorrelation  |  {symbol} {tf}  ({session})", fontsize=13, fontweight="bold")
    n = len(r)
    ci_band = 1.96 / np.sqrt(n)

    for ax, (s_name, s) in zip(axes, [("Returns r_t", r),
                                       ("|Returns| (vol clustering)", np.abs(r)),
                                       ("Squared returns (ARCH effect)", r**2)]):
        if HAS_STATSMODELS:
            try:
                acf_vals, confint = acf(s, nlags=20, alpha=0.05, fft=True)
                lags    = acf_vals[1:21]
                lb = acorr_ljungbox(s, lags=[20], return_df=True)
                lb_p = float(lb["lb_pvalue"].iloc[0])
            except Exception:
                lags = _manual_acf(s, 20)
                lb_p = None
        else:
            lags = _manual_acf(s, 20)
            lb_p = None

        x = np.arange(1, 21)
        ax.bar(x, lags, color=np.where(np.abs(lags) > ci_band, "#E53935", "#90CAF9"),
               edgecolor="none", alpha=0.8)
        ax.axhline(ci_band, linestyle="--", color="gray", linewidth=0.8, alpha=0.7)
        ax.axhline(-ci_band, linestyle="--", color="gray", linewidth=0.8, alpha=0.7)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xlabel("Lag")
        ax.set_ylabel("ACF")
        title_extra = f" | LB(20) p={lb_p:.4f}" if lb_p is not None else ""
        ax.set_title(f"{s_name}{title_extra}")
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0.5, 20.5)

    plt.tight_layout()
    return _savefig(fig, f"acf_{symbol}_{tf}_{session}")


def plot_hourly_vol(all_hourly: Dict, symbol: str) -> str:
    """Bar chart of mean absolute return by UTC hour for the given instrument."""
    hours_all = sorted(all_hourly.keys(), key=int)
    if not hours_all:
        return ""

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle(f"Intraday Seasonality  |  {symbol} (H1, All Sessions)", fontsize=13, fontweight="bold")

    # Top: mean abs return by hour
    ax1 = axes[0]
    vals_abs = [all_hourly[h]["mean_abs_r"] for h in hours_all]
    hours_int = [int(h) for h in hours_all]
    colors = ["#E53935" if 7 <= h <= 10 or 13 <= h <= 17 else "#90CAF9" for h in hours_int]
    ax1.bar(hours_int, vals_abs, color=colors, edgecolor="none", alpha=0.85)
    ax1.set_xlabel("UTC Hour")
    ax1.set_ylabel("Mean |r_t|  (log return)")
    ax1.set_title("Mean Absolute Return by Hour  (red = kill zone hours)")
    ax1.set_xticks(range(0, 24))
    ax1.grid(True, alpha=0.3, axis="y")

    # Bottom: mean signed return by hour
    ax2 = axes[1]
    vals_signed = [all_hourly[h]["mean_r"] for h in hours_all]
    colors2 = ["#4CAF50" if v >= 0 else "#E53935" for v in vals_signed]
    ax2.bar(hours_int, vals_signed, color=colors2, edgecolor="none", alpha=0.85)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_xlabel("UTC Hour")
    ax2.set_ylabel("Mean r_t  (log return)")
    ax2.set_title("Mean Signed Return by Hour")
    ax2.set_xticks(range(0, 24))
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    return _savefig(fig, f"hourly_{symbol}")


def plot_tail_comparison(r: np.ndarray, symbol: str, tf: str) -> str:
    """Empirical tail vs Normal, Student-t, and fitted GPD on log-log scale."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"Tail Comparison  |  {symbol} {tf}", fontsize=13, fontweight="bold")

    r_std  = (r - r.mean()) / r.std()
    n      = len(r_std)

    for ax, title, tail in zip(axes, ["Upper Tail", "Lower Tail"], ["upper", "lower"]):
        if tail == "upper":
            data = np.sort(r_std)
        else:
            data = np.sort(-r_std)

        # Empirical exceedance probabilities
        exceedances  = data[data > 0]
        if len(exceedances) < 10:
            ax.set_title(f"{title}: no data")
            continue
        # Rank from highest
        sorted_exc = np.sort(exceedances)[::-1]
        emp_probs  = np.arange(1, len(sorted_exc) + 1) / n

        ax.scatter(sorted_exc, emp_probs, s=3, alpha=0.5, color="#2196F3",
                   label="Empirical", zorder=3, rasterized=True)

        x_range = np.linspace(sorted_exc.min(), sorted_exc.max() * 1.2, 200)

        # Normal tail
        ax.plot(x_range, stats.norm.sf(x_range), "g--", linewidth=1.5,
                label="Normal", alpha=0.8)

        # Student-t fit
        try:
            df_t, loc_t, scale_t = stats.t.fit(exceedances)
            ax.plot(x_range, stats.t.sf(x_range, df=df_t, loc=loc_t, scale=scale_t),
                    "orange", linewidth=1.5, linestyle="--", label=f"Student-t (df={df_t:.1f})", alpha=0.8)
        except Exception:
            pass

        # GPD fit
        try:
            u = float(np.percentile(exceedances, 80))   # threshold
            exc_over_u = exceedances[exceedances > u] - u
            if len(exc_over_u) >= MIN_OBS_GPD:
                xi_g, _, sigma_g = genpareto.fit(exc_over_u, floc=0)
                x_gpd = np.linspace(0, x_range.max() - u, 200)
                # P(X > u + y) for y > 0
                p_exceed_u = len(exc_over_u) / n
                gpd_sf = p_exceed_u * genpareto.sf(x_gpd, xi_g, loc=0, scale=sigma_g)
                ax.plot(x_gpd + u, gpd_sf, "r-", linewidth=2,
                        label=f"GPD (ξ={xi_g:.3f})", alpha=0.9)
        except Exception:
            pass

        ax.set_yscale("log")
        ax.set_xlabel("Standardised Threshold z")
        ax.set_ylabel("P(|r| > z)  [log scale]")
        ax.set_title(title)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return _savefig(fig, f"tails_{symbol}_{tf}")


def plot_garch_vol(r: np.ndarray, symbol: str, tf: str) -> str:
    """Plot conditional volatility from GARCH(1,1) overlaid on returns."""
    if not HAS_ARCH or len(r) < MIN_OBS_GARCH:
        return ""
    try:
        r_pct = r * 100.0
        am    = arch_model(r_pct, vol="GARCH", p=1, q=1, dist="Normal", rescale=False)
        res   = am.fit(disp="off", show_warning=False, options={"maxiter": 1000})
        cond_vol = res.conditional_volatility / 100.0   # back to log return units

        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        fig.suptitle(f"GARCH(1,1) Conditional Volatility  |  {symbol} {tf}", fontsize=13)

        axes[0].plot(r, color="#90CAF9", linewidth=0.4, alpha=0.8)
        axes[0].set_ylabel("Log Return")
        axes[0].grid(True, alpha=0.3)
        axes[0].set_title("Returns")

        axes[1].plot(cond_vol, color="#E53935", linewidth=0.6)
        axes[1].set_ylabel("Conditional σ")
        axes[1].grid(True, alpha=0.3)
        persist = res.params.get("alpha[1]", 0) + res.params.get("beta[1]", 0)
        axes[1].set_title(f"GARCH Conditional Volatility  (α+β = {float(persist):.4f})")

        plt.tight_layout()
        return _savefig(fig, f"garch_{symbol}_{tf}")
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALY DETECTION (aggregate all findings)
# ═══════════════════════════════════════════════════════════════════════════════

def collect_anomalies(full_results: Dict) -> list:
    """
    Scan all results and return a list of anomaly dicts representing statistically
    significant deviations from a Gaussian random walk.
    """
    anomalies = []

    for symbol, sym_data in full_results.get("instruments", {}).items():
        tx_cost = TX_COST_BPS.get(symbol, 4)
        for tf, tf_data in sym_data.items():
            for session, data in tf_data.items():
                nbpy = BARS_PER_YEAR.get(tf, 6240)

                # Helper to add an anomaly
                def add(description, test, stat, p_val, edge_bps=None, stable=None, extra=None):
                    surv_bonf = bool(p_val < BONFERRONI_ALPHA) if p_val is not None else False
                    econ_sig  = (abs(edge_bps) > tx_cost) if edge_bps is not None else None
                    anomalies.append({
                        "instrument":   symbol, "timeframe": tf, "session": session,
                        "description":  description, "test": test,
                        "statistic":    _safe(stat), "p_value": _safe(p_val),
                        "survives_bonferroni": surv_bonf,
                        "edge_bps":     _safe(edge_bps),
                        "economically_significant": econ_sig,
                        "stable_across_years": stable,
                        "notes":        extra or "",
                    })

                # ── Non-normality ─────────────────────────────────────────────
                nm = data.get("normality", {})
                jb = nm.get("jarque_bera", {})
                if jb.get("p_value") is not None and jb["p_value"] < 0.05:
                    ku = data.get("moments", {}).get("excess_kurtosis", 0) or 0
                    sk = data.get("moments", {}).get("skewness", 0) or 0
                    add(f"Non-normal distribution (excess kurtosis={ku:.2f}, skew={sk:.3f})",
                        "Jarque-Bera", jb["statistic"], jb["p_value"])

                # ── ACF anomalies ─────────────────────────────────────────────
                acf_data = data.get("acf", {})
                # Return ACF significant lags → potential directional edge
                ret_acf = acf_data.get("returns", {})
                sig_lags_r = ret_acf.get("significant_lags", [])
                if sig_lags_r:
                    lb = ret_acf.get("ljung_box", {})
                    lb5 = lb.get("lag5", {}).get("p_value") if lb else None
                    acf_vals = ret_acf.get("acf_lags_1_20", [])
                    std_pp = data.get("moments", {}).get("std_per_period", 0) or 0
                    max_rho = max((abs(acf_vals[i-1]) for i in sig_lags_r if 0 < i <= len(acf_vals)), default=0)
                    # Edge estimate: ρ × 0.8 × σ × 10000 bps
                    edge = max_rho * 0.8 * std_pp * 10000
                    add(f"Significant return ACF at lags {sig_lags_r} — linear directional predictability",
                        "ACF+LjungBox", max_rho, lb5 or 0.05, edge_bps=edge,
                        extra=f"max|ρ|={max_rho:.4f}, est. edge={edge:.2f} bps vs {tx_cost} bps cost")

                # Absolute return ACF → volatility clustering
                abs_acf = acf_data.get("abs_returns", {})
                sig_lags_abs = abs_acf.get("significant_lags", [])
                if sig_lags_abs:
                    lb_abs = abs_acf.get("ljung_box", {})
                    lb5_abs = lb_abs.get("lag5", {}).get("p_value") if lb_abs else None
                    max_rho_abs = max((abs(abs_acf.get("acf_lags_1_20", [0])[i-1])
                                       for i in sig_lags_abs if 0 < i <= 20), default=0)
                    add(f"Significant |return| ACF at lags {sig_lags_abs[:5]} — volatility is predictable",
                        "ACF(|r|)+LjungBox", max_rho_abs, lb5_abs or 0.05,
                        extra="Volatility clustering confirmed; informs position sizing")

                # ── GARCH persistence ─────────────────────────────────────────
                garch = data.get("garch", {})
                g11   = garch.get("garch11", {})
                if isinstance(g11, dict) and g11.get("persistence") is not None:
                    pers = g11["persistence"]
                    if pers > 0.90:
                        hl = g11.get("half_life_periods")
                        add(f"GARCH persistence={pers:.4f} — strong volatility clustering",
                            "GARCH(1,1)", pers, None,
                            extra=f"Half-life={hl:.1f} periods" if hl else "")

                # ── EGARCH leverage effect ────────────────────────────────────
                egarch = garch.get("egarch", {})
                if isinstance(egarch, dict):
                    gamma = egarch.get("gamma")
                    if gamma is not None and gamma < -0.02:
                        add(f"EGARCH leverage effect: γ={gamma:.4f} (down moves → more vol)",
                            "EGARCH gamma", gamma, None,
                            extra="SHORT setups operate in higher realized vol than LONG setups")

                # ── Jump post-return predictability ──────────────────────────
                jmp = data.get("jumps", {})
                pjr = jmp.get("post_jump_returns", {})
                for lag_k, lag_data in pjr.items():
                    if not isinstance(lag_data, dict):
                        continue
                    pv = lag_data.get("p_value")
                    mn = lag_data.get("mean")
                    if pv is not None and pv < 0.05 and mn is not None:
                        interp = lag_data.get("interpretation", "")
                        edge   = abs(mn) * 10000
                        add(f"Post-jump {lag_k}: mean direction-adjusted return ≠ 0 ({interp})",
                            "t-test post-jump", mn, pv, edge_bps=edge,
                            extra=f"After |z|>{JUMP_SIGMA_THRESHOLD} jump, mean lag return={mn:.6f}")

                # ── Intraday seasonality ──────────────────────────────────────
                intra = data.get("intraday", {})
                kw_p = intra.get("kruskal_wallis_p_value")
                if kw_p is not None and kw_p < 0.05:
                    add("Intraday volatility seasonality — different hours have different distributions",
                        "Kruskal-Wallis", intra.get("kruskal_wallis_statistic"), kw_p,
                        extra=f"Peak vol hour: UTC {intra.get('peak_abs_return_hour_utc')}")

                # ── Conditional: session open vs mid-session ──────────────────
                cond = data.get("conditional", {})
                spos = cond.get("by_session_position", {})
                if isinstance(spos, dict) and spos.get("p_value") is not None and spos["p_value"] < 0.05:
                    diff = spos.get("mean_diff", 0) or 0
                    edge = abs(diff) * 10000
                    add("Session-open bars have significantly different return distribution",
                        "Welch t-test (session position)", diff, spos["p_value"], edge_bps=edge,
                        extra=f"Open bar mean={spos.get('group1_mean'):.6f} vs mid={spos.get('group2_mean'):.6f}")

                # ── Fat-tail excess over Gaussian ─────────────────────────────
                tails = data.get("tails", {})
                ratio3 = tails.get("sigma3_excess_ratio")
                if ratio3 is not None and ratio3 > 2.0:
                    add(f"Fat tails: {ratio3:.1f}× more 3-sigma events than Gaussian predicts",
                        "Empirical sigma-event count", ratio3, None,
                        extra=f"Implies SL hit rate ~{ratio3:.1f}× higher than Gaussian-calibrated SL")

    # Deduplicate and sort by p_value
    seen = set()
    deduped = []
    for a in anomalies:
        key = (a["instrument"], a["timeframe"], a["session"], a["description"][:60])
        if key not in seen:
            seen.add(key)
            deduped.append(a)

    deduped.sort(key=lambda x: (x.get("p_value") or 1.0, -abs(x.get("edge_bps") or 0)))
    return deduped


# ═══════════════════════════════════════════════════════════════════════════════
# GTOS IMPLICATIONS WRITER
# ═══════════════════════════════════════════════════════════════════════════════

def build_gtos_implications(full_results: Dict, anomalies: list) -> Dict:
    """Answer the 6 GTOS-specific questions from the analysis results."""

    gold_h1 = full_results.get("instruments", {}).get("XAUUSD", {}).get("H1", {}).get("All", {})

    # ── 1. Tail analysis vs SL placement ─────────────────────────────────────
    tails = gold_h1.get("tails", {})
    lower = tails.get("lower", {})
    xi    = lower.get("gpd_shape_xi")
    q1    = lower.get("q_1pct")     # 1% worst hourly move (in log return units)
    q005  = lower.get("q_0.5pct")

    # Current SL policy: max(zone_height, $10, 1.5 × M15_ATR)
    # Rough M15 ATR for gold ≈ 0.0005 in log return terms (0.05% of price per 15min)
    sl_tail_text = "DATA UNAVAILABLE"
    if xi is not None and q1 is not None:
        q1_bps = q1 * 10000
        xi_interp = "FAT" if xi > 0.05 else "NEAR-GAUSSIAN"
        sl_tail_text = (
            f"Gold H1 lower tail: GPD shape ξ={xi:.4f} ({xi_interp}). "
            f"The 1%-quantile worst hourly move is {q1_bps:.1f} bps ({q1*100:.4f}% of price). "
            f"For a $3,000 gold price, this is ~${q1*3000:.2f}/oz per hour. "
            f"If your typical H1 SL is ~0.10-0.30% (~$3-9/oz), the 1% worst move "
            f"{'LIKELY EXCEEDS your SL' if q1 > 0.003 else 'is within your SL range'}. "
            f"Fat tails (ξ={xi:.3f}) confirm that Gaussian-calibrated SLs will be hit "
            f"more frequently than expected: {tails.get('sigma3_excess_ratio', 'N/A')}× more 3σ events/year."
        )

    # ── 2. Volatility clustering ──────────────────────────────────────────────
    garch_data = gold_h1.get("garch", {}).get("garch11", {})
    pers       = garch_data.get("persistence")
    hl         = garch_data.get("half_life_periods")

    vol_cluster_text = "DATA UNAVAILABLE (GARCH not fitted)"
    if pers is not None:
        if hl is not None:
            hl_days = hl / BARS_PER_YEAR["H1"] * 261
            hl_text  = f"~{hl:.1f} H1 bars ({hl_days:.2f} trading days)"
        else:
            hl_text = "undefined (unit-root volatility)"
        vol_cluster_text = (
            f"GARCH(1,1) persistence α+β={pers:.4f}. "
            f"Half-life of volatility shocks: {hl_text}. "
            f"{'VERY STRONG clustering' if pers > 0.97 else 'STRONG clustering' if pers > 0.92 else 'MODERATE clustering'}. "
            f"A volatile session today implies ~{(pers**24)*100:.1f}% of that excess vol persists to same time tomorrow "
            f"(24 H1 bars forward). "
            f"IMPLICATION: Pre-trade ATR-based position sizing is warranted; "
            f"a quiet day can be followed by an explosive one."
        )

    # ── 3. Autocorrelation at trading horizon ─────────────────────────────────
    acf_block = gold_h1.get("acf", {})
    acf_data  = acf_block.get("returns", {})
    bartlett  = acf_block.get("bartlett_ci_95", 0)
    sig_lags  = acf_data.get("significant_lags", [])
    acf_lags  = acf_data.get("acf_lags_1_20", [])
    lag1_rho  = acf_lags[0] if acf_lags else None
    lag4_rho  = acf_lags[3] if len(acf_lags) >= 4 else None

    acf_text = "DATA UNAVAILABLE"
    if acf_lags:
        trading_horizon_lags = [i for i in sig_lags if 1 <= i <= 4]
        lag4_str = f"{lag4_rho:.4f}" if lag4_rho is not None else "N/A"
        lag1_str = f"{lag1_rho:.4f}" if lag1_rho is not None else "N/A"
        acf_text = (
            f"Gold H1 return ACF: lag1={lag1_str}, lag4={lag4_str}. "
            f"Significant lags (outside Bartlett ±{bartlett:.4f}): {sig_lags or 'none'}. "
            f"Lags 1-4 (our trading horizon 1-4 H1 candles): {'SIGNIFICANT at ' + str(trading_horizon_lags) if trading_horizon_lags else 'NO significant ACF'}. "
            + (f"This provides {'INDEPENDENT CONFIRMATION' if trading_horizon_lags else 'NO linear evidence'} "
               f"for the OB retest mechanism's {len(trading_horizon_lags)}-lag predictability window. "
               f"Note: economic value is limited ({abs(lag1_rho or 0)*0.8*float(gold_h1.get('moments',{}).get('std_per_period') or 0.001)*10000:.2f} bps "
               f"vs ~4 bps spread + slippage).")
        )

    # ── 4. Post-jump behavior ─────────────────────────────────────────────────
    gold_h1_jumps = gold_h1.get("jumps", {})
    pjr = gold_h1_jumps.get("post_jump_returns", {})
    jump_text = "DATA UNAVAILABLE (insufficient jumps detected)"
    if pjr:
        lag1_jump = pjr.get("lag_1", {})
        interp1   = lag1_jump.get("interpretation", "UNKNOWN")
        mn1       = lag1_jump.get("mean")
        pv1       = lag1_jump.get("p_value")
        jump_text = (
            f"Post-jump returns (H1, direction-adjusted): "
            f"lag1 mean={mn1:.6f} ({interp1}), p={pv1:.4f}. "
            f"Jump frequency: {gold_h1_jumps.get('jump_frequency_per_day', 0):.3f} jumps/day. "
            f"Peak jump hour: UTC {gold_h1_jumps.get('peak_jump_hour_utc', 'N/A')}. "
            + (f"Post-jump {'REVERSION supports' if interp1 == 'REVERSION' else 'CONTINUATION challenges'} "
               f"the sweep-and-revert hypothesis (OB retest as stop-cascade mean-reversion to pre-cascade equilibrium). "
               f"{'This is independent statistical support for the edge mechanism.' if interp1 == 'REVERSION' and pv1 and pv1 < 0.05 else 'Result not statistically significant at 5% level.'}")
        )

    # ── 5. Leverage effect ────────────────────────────────────────────────────
    egarch = gold_h1.get("garch", {}).get("egarch", {})
    gamma  = egarch.get("gamma")
    lev_text = "DATA UNAVAILABLE (EGARCH not fitted)"
    if gamma is not None:
        lev_text = (
            f"EGARCH gamma (asymmetry) = {gamma:.4f}. "
            f"{'LEVERAGE EFFECT CONFIRMED' if gamma < -0.02 else 'NO significant leverage effect'}. "
            + (f"Down moves produce ~{abs(gamma)*100:.1f}% more vol than equivalent up moves. "
               f"GTOS implication: SHORT setups on XAUUSD face higher realized volatility after entry, "
               f"implying the SL-to-TP ratio for shorts should be more conservative than for longs. "
               f"This is consistent with gold's asymmetric crisis behavior." if gamma < -0.02 else
               f"Gold volatility is symmetric — LONG and SHORT setups have similar post-entry vol profiles.")
        )

    # ── 6. Best hours for edge ────────────────────────────────────────────────
    intra = gold_h1.get("intraday", {})
    by_h  = intra.get("by_hour", {})
    hour_text = "DATA UNAVAILABLE"
    if by_h:
        # Sort by mean absolute return descending
        sorted_hours = sorted(by_h.items(), key=lambda x: x[1].get("mean_abs_r", 0) or 0, reverse=True)
        top5 = [(int(h), v.get("mean_abs_r", 0), v.get("mean_r", 0)) for h, v in sorted_hours[:5]]
        kz_hours = list(range(7, 11)) + list(range(13, 17))   # XAUUSD KZ hours
        kz_rank  = sorted([(h, v.get("mean_abs_r", 0)) for h, v in by_h.items()
                           if int(h) in kz_hours],
                          key=lambda x: x[1], reverse=True)
        hour_text = (
            f"Top-5 absolute return hours (UTC): {[(h, f'{v*10000:.2f}bps') for h,v,_ in top5]}. "
            f"Kill zone hours ranked by vol: {[(int(h), f'{v*10000:.2f}bps') for h,v in kz_rank[:4]]}. "
            f"Kruskal-Wallis p={intra.get('kruskal_wallis_p_value',1.0):.6f} — "
            f"{'hourly distributions ARE significantly different' if intra.get('kw_significant_p05') else 'no significant hourly seasonality'}. "
            f"GTOS kill zones {'align well with' if any(int(h) in kz_hours for h,_,_ in top5[:3]) else 'do NOT match'} "
            f"the highest-volatility hours."
        )

    return {
        "q1_tail_vs_sl_placement":             sl_tail_text,
        "q2_volatility_clustering":            vol_cluster_text,
        "q3_acf_at_trading_horizon_1_4_H1":    acf_text,
        "q4_post_jump_behavior":               jump_text,
        "q5_leverage_effect_long_vs_short":    lev_text,
        "q6_best_hours_by_edge_potential":     hour_text,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MARKDOWN SUMMARY WRITER
# ═══════════════════════════════════════════════════════════════════════════════

def write_summary(full_results: Dict, anomalies: list, implications: Dict,
                  ts: str) -> str:
    lines = []
    A = lines.append

    A(f"# GTOS Distributional Characterization — Summary")
    A(f"")
    A(f"**Generated:** {ts} UTC")
    A(f"**Method:** Full statistical characterization — moments, normality, GPD tails, ACF, GARCH, jumps, intraday seasonality, conditional distributions")
    A(f"**Bonferroni threshold:** α* = {BONFERRONI_ALPHA:.6f}  ({N_TOTAL_TESTS} total tests)")
    A(f"")
    A(f"---")
    A(f"")

    # ── GTOS IMPLICATIONS ─────────────────────────────────────────────────────
    A(f"## GTOS IMPLICATIONS (XAUUSD H1 unless noted)")
    A(f"")
    for qnum, (key, val) in enumerate(implications.items(), 1):
        label = key.replace("_", " ").upper()
        A(f"### Q{qnum}: {label}")
        A(f"")
        A(f"{val}")
        A(f"")

    A(f"---")
    A(f"")

    # ── TRADEABLE ANOMALIES ───────────────────────────────────────────────────
    A(f"## TRADEABLE ANOMALIES")
    A(f"")
    A(f"Only findings with p < 0.05 are listed.  "
      f"**Bold** = survives Bonferroni (p < {BONFERRONI_ALPHA:.5f}).  "
      f"★ = economically significant (edge > transaction cost).")
    A(f"")

    if not anomalies:
        A(f"*No significant anomalies detected.*")
    else:
        # Group by instrument
        by_instr: Dict[str, list] = {}
        for a in anomalies:
            by_instr.setdefault(a["instrument"], []).append(a)

        for sym, alist in by_instr.items():
            A(f"### {sym}")
            A(f"")
            A(f"| TF | Session | Finding | p-value | Bonferroni | Edge (bps) | Econ Sig | Stable |")
            A(f"|---|---|---|---|---|---|---|---|")
            for a in alist:
                p_str = f"{a['p_value']:.4f}" if a.get("p_value") is not None else "—"
                bonf  = "**YES**" if a.get("survives_bonferroni") else "no"
                e_str = f"{a['edge_bps']:.2f}" if a.get("edge_bps") is not None else "—"
                ec    = "★ YES" if a.get("economically_significant") else ("no" if a.get("edge_bps") is not None else "—")
                st    = str(a.get("stable_across_years", "—"))
                desc  = a["description"][:80]
                A(f"| {a['timeframe']} | {a['session']} | {desc} | {p_str} | {bonf} | {e_str} | {ec} | {st} |")
            A(f"")

    A(f"---")
    A(f"")

    # ── PER-INSTRUMENT SUMMARY TABLES ─────────────────────────────────────────
    A(f"## Per-Instrument Summary — H1 'All Sessions'")
    A(f"")
    A(f"| Instrument | n_returns | Mean (ann.) | Std (ann.) | Skewness | Ex.Kurt | JB p | AD 5% | GARCH α+β | Tail ξ (lower) | 3σ×/yr (emp) | 3σ×/yr (norm) |")
    A(f"|---|---|---|---|---|---|---|---|---|---|---|---|")

    for sym in INSTRUMENTS:
        data = full_results.get("instruments", {}).get(sym, {}).get("H1", {}).get("All", {})
        if not data:
            A(f"| {sym} | N/A | — | — | — | — | — | — | — | — | — | — |")
            continue
        m    = data.get("moments", {})
        nm   = data.get("normality", {})
        gd   = data.get("garch", {}).get("garch11", {})
        tl   = data.get("tails", {})

        n_r  = m.get("n", "—")
        mn_a = f"{m.get('mean_annualized', 0)*100:.4f}%" if m.get("mean_annualized") else "—"
        sd_a = f"{m.get('std_annualized', 0)*100:.2f}%" if m.get("std_annualized") else "—"
        sk   = f"{m.get('skewness', 0):.3f}" if m.get("skewness") is not None else "—"
        ku   = f"{m.get('excess_kurtosis', 0):.3f}" if m.get("excess_kurtosis") is not None else "—"
        jb_p = f"{nm.get('jarque_bera', {}).get('p_value', 1):.2e}" if nm.get("jarque_bera") else "—"
        ad   = "REJ" if nm.get("anderson_darling", {}).get("reject_at_5pct") else "OK"
        gp   = f"{gd.get('persistence'):.4f}" if gd.get("persistence") is not None else "—"
        xi   = f"{tl.get('lower', {}).get('gpd_shape_xi'):.4f}" if tl.get("lower", {}).get("gpd_shape_xi") is not None else "—"
        s3e  = f"{tl.get('sigma3_events_per_year_empirical'):.1f}" if tl.get("sigma3_events_per_year_empirical") is not None else "—"
        s3n  = f"{tl.get('sigma3_events_per_year_gaussian'):.1f}" if tl.get("sigma3_events_per_year_gaussian") is not None else "—"

        A(f"| {sym} | {n_r} | {mn_a} | {sd_a} | {sk} | {ku} | {jb_p} | {ad} | {gp} | {xi} | {s3e} | {s3n} |")

    A(f"")
    A(f"---")
    A(f"")

    # ── M15 SUMMARY ──────────────────────────────────────────────────────────
    A(f"## Per-Instrument Summary — M15 'All Sessions'")
    A(f"")
    A(f"| Instrument | n_returns | Std (ann.) | Ex.Kurt | JB p | GARCH α+β | 3σ×/yr (emp) |")
    A(f"|---|---|---|---|---|---|---|")
    for sym in INSTRUMENTS:
        data = full_results.get("instruments", {}).get(sym, {}).get("M15", {}).get("All", {})
        if not data:
            A(f"| {sym} | N/A | — | — | — | — | — |")
            continue
        m  = data.get("moments", {})
        nm = data.get("normality", {})
        gd = data.get("garch", {}).get("garch11", {})
        tl = data.get("tails", {})

        n_r  = m.get("n", "—")
        sd_a = f"{m.get('std_annualized', 0)*100:.2f}%" if m.get("std_annualized") else "—"
        ku   = f"{m.get('excess_kurtosis', 0):.3f}" if m.get("excess_kurtosis") is not None else "—"
        jb_p = f"{nm.get('jarque_bera', {}).get('p_value', 1):.2e}" if nm.get("jarque_bera") else "—"
        gp   = f"{gd.get('persistence'):.4f}" if gd.get("persistence") is not None else "—"
        s3e  = f"{tl.get('sigma3_events_per_year_empirical'):.1f}" if tl.get("sigma3_events_per_year_empirical") is not None else "—"
        A(f"| {sym} | {n_r} | {sd_a} | {ku} | {jb_p} | {gp} | {s3e} |")

    A(f"")
    A(f"---")
    A(f"")
    A(f"*Generated by GTOS Engineering Agent — research/diagnostics/run_distributional_analysis.py*")

    md_path = os.path.join(OUT_DIR, f"distributional_summary_{ts}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return md_path


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_single(symbol: str, tf: str, df: pd.DataFrame) -> Dict:
    """Run all analyses for one instrument × timeframe combination across all sessions."""
    r_all, t_all = compute_log_returns(df, tf)
    n = len(r_all)
    print(f"  {symbol} {tf}: n={n} returns, {str(t_all[0])[:10]} – {str(t_all[-1])[:10]}")

    sessions = ["All"] + list(KILL_ZONES.get(symbol, {}).keys())
    tf_result = {}

    for session in sessions:
        r_s, t_s = filter_session(r_all, t_all, symbol, session)
        if len(r_s) < MIN_OBS_BASIC:
            print(f"    {session}: only {len(r_s)} returns — skip")
            continue
        print(f"    {session}: n={len(r_s)}")

        skip_garch = (tf == "D1") or (len(r_s) < MIN_OBS_GARCH)

        s_data: Dict = {
            "n":       len(r_s),
            "date_start": str(t_s[0])[:19],
            "date_end":   str(t_s[-1])[:19],
        }

        # a) Moments
        try:
            s_data["moments"] = analyze_moments(r_s, tf)
        except Exception as e:
            s_data["moments"] = {"error": str(e)}

        # b) Normality
        try:
            s_data["normality"] = analyze_normality(r_s)
        except Exception as e:
            s_data["normality"] = {"error": str(e)}

        # c) Tails
        try:
            s_data["tails"] = analyze_tails(r_s, tf)
        except Exception as e:
            s_data["tails"] = {"error": str(e)}

        # d) ACF
        try:
            s_data["acf"] = analyze_acf(r_s)
        except Exception as e:
            s_data["acf"] = {"error": str(e)}

        # e) GARCH
        if not skip_garch:
            try:
                s_data["garch"] = analyze_garch(r_s)
            except Exception as e:
                s_data["garch"] = {"error": str(e)}
        else:
            s_data["garch"] = {"status": "skipped (D1 or n_insufficient)"}

        # f) Jumps
        try:
            s_data["jumps"] = analyze_jumps(r_s, t_s, tf)
        except Exception as e:
            s_data["jumps"] = {"error": str(e)}

        # g) Intraday seasonality (only meaningful for sub-daily)
        if tf != "D1" and session == "All":
            try:
                s_data["intraday"] = analyze_intraday(r_s, t_s)
            except Exception as e:
                s_data["intraday"] = {"error": str(e)}

        # h) Conditional distributions (H1 and M15 only)
        if tf != "D1":
            try:
                s_data["conditional"] = analyze_conditional(r_s, t_s, df, symbol, tf)
            except Exception as e:
                s_data["conditional"] = {"error": str(e)}

        # i) Year-by-year stability
        try:
            s_data["stability_by_year"] = analyze_stability(r_s, t_s)
        except Exception as e:
            s_data["stability_by_year"] = {"error": str(e)}

        tf_result[session] = s_data

    return tf_result


def main():
    print("=" * 70)
    print("GTOS Distributional Characterization Analysis")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 70)

    np.random.seed(42)   # reproducible bootstrap

    full_results = {
        "metadata": {
            "generated_at":       TIMESTAMP + " UTC",
            "n_bootstrap":        N_BOOT,
            "max_bootstrap_n":    MAX_BOOT_N,
            "bonferroni_alpha":   BONFERRONI_ALPHA,
            "n_total_tests":      N_TOTAL_TESTS,
            "jump_sigma_threshold": JUMP_SIGMA_THRESHOLD,
            "gpd_threshold_pct":  GPD_THRESHOLD_PCT,
            "tx_costs_bps":       TX_COST_BPS,
            "bars_per_year":      BARS_PER_YEAR,
        },
        "instruments": {},
    }

    # ── Instrument loop ───────────────────────────────────────────────────────
    for symbol, conf in INSTRUMENTS.items():
        print(f"\n{'━'*60}")
        print(f"Instrument: {symbol}")
        print(f"{'━'*60}")
        sym_result = {}

        for tf in conf["tfs"]:
            print(f"\n  Timeframe: {tf}")
            df = load_ohlcv(symbol, tf)
            if df is None:
                print(f"  NO DATA FILE for {symbol} {tf} — skipping")
                continue

            try:
                sym_result[tf] = run_single(symbol, tf, df)
            except Exception as e:
                print(f"  ERROR: {e}")
                traceback.print_exc()
                sym_result[tf] = {"error": str(e)}

            # ── Generate plots (H1 and M15 only to limit output) ──────────────
            if tf in ["H1", "M15"]:
                r_plot, t_plot = compute_log_returns(df, tf)
                if len(r_plot) >= MIN_OBS_BASIC:
                    try:
                        plot_qq(r_plot, symbol, tf, "All")
                        print(f"    [plot] QQ saved")
                    except Exception as e:
                        print(f"    [plot] QQ failed: {e}")
                    try:
                        plot_acf_panel(r_plot, symbol, tf, "All")
                        print(f"    [plot] ACF saved")
                    except Exception as e:
                        print(f"    [plot] ACF failed: {e}")
                    try:
                        plot_tail_comparison(r_plot, symbol, tf)
                        print(f"    [plot] Tails saved")
                    except Exception as e:
                        print(f"    [plot] Tails failed: {e}")
                    if tf == "H1":
                        try:
                            plot_garch_vol(r_plot, symbol, tf)
                            print(f"    [plot] GARCH vol saved")
                        except Exception as e:
                            print(f"    [plot] GARCH failed: {e}")

        full_results["instruments"][symbol] = sym_result

        # ── Hourly seasonality plot (uses H1 data) ────────────────────────────
        try:
            h1_intra = sym_result.get("H1", {}).get("All", {}).get("intraday", {})
            by_hour  = h1_intra.get("by_hour")
            if by_hour:
                plot_hourly_vol(by_hour, symbol)
                print(f"  [plot] Hourly vol saved for {symbol}")
        except Exception as e:
            print(f"  [plot] Hourly vol failed: {e}")

    # ── Collect anomalies ─────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("Collecting anomalies...")
    anomalies = collect_anomalies(full_results)
    full_results["tradeable_anomalies"] = anomalies
    print(f"  Found {len(anomalies)} findings (p < 0.05)")
    bonf_count = sum(1 for a in anomalies if a.get("survives_bonferroni"))
    econ_count = sum(1 for a in anomalies if a.get("economically_significant"))
    print(f"  Bonferroni-surviving: {bonf_count}")
    print(f"  Economically significant: {econ_count}")

    # ── GTOS implications ─────────────────────────────────────────────────────
    print("Building GTOS implications...")
    implications = build_gtos_implications(full_results, anomalies)
    full_results["gtos_implications"] = implications

    # ── Write JSON ────────────────────────────────────────────────────────────
    json_path = os.path.join(OUT_DIR, f"distributional_characterization_{TIMESTAMP}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, cls=_NpEncoder, indent=2)
    print(f"\nJSON saved: {json_path}")

    # ── Write Markdown summary ────────────────────────────────────────────────
    md_path = write_summary(full_results, anomalies, implications, TIMESTAMP)
    print(f"Summary saved: {md_path}")

    print(f"\n{'='*70}")
    print(f"DONE — {len(anomalies)} anomalies catalogued")
    print(f"  Plots directory: {PLOTS_DIR}")
    print(f"  JSON:    {json_path}")
    print(f"  Summary: {md_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
