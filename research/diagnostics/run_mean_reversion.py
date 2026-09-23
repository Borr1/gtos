#!/usr/bin/env python3
"""
GTOS Mean-Reversion Mechanics Analysis
=======================================
Three complementary tests characterising mean-reversion properties for all
5 GTOS instruments.  Results directly inform trailing stop optimisation.

TEST A1: Ornstein-Uhlenbeck Half-Life (Q-6.3)
  ADF regression on SMA-detrended price levels.
  Multiple detrend windows, year splits, kill-zone subsample.

TEST A2: Fractional Integration / Hurst (Q-15.2)
  GPH log-periodogram (two bandwidths) + Whittle MLE + R/S + DFA.
  Applied to log-return series so the estimators work on a near-stationary
  input.

TEST A3: Compression-Before-Expansion (Q-0.4)
  ATR compression threshold → forward ATR ratio.
  Mann-Whitney U, ATR autocorrelation, AR(1) control for GARCH persistence.

Outputs
-------
  research/diagnostics/mean_reversion_mechanics/
      mean_reversion_results_<ts>.json
      mean_reversion_summary_<ts>.md
      plots/

Usage
-----
  python research/diagnostics/run_mean_reversion.py

Notes
-----
  - Reuses CSV files from data/historical/ (same format as prior diagnostics)
  - Bonferroni correction across ~260 hypothesis tests (α* ≈ 0.000192)
  - Never modifies src/ or prompts/
"""

import os
import sys
import json
import warnings
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
from scipy.stats import mannwhitneyu

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import acf as sm_acf
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("WARNING: statsmodels not available — OU and ATR ACF will be skipped.")

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR  = os.path.join(REPO_ROOT, "data", "historical")
OUT_DIR   = os.path.join(os.path.dirname(__file__), "mean_reversion_mechanics")
PLOTS_DIR = os.path.join(OUT_DIR, "plots")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

TIMESTAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

INSTRUMENTS = {
    "XAUUSD": "XAUUSD",
    "US30":   "US30_cash",
    "USDJPY": "USDJPY",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
}

# Kill zones in UTC fractional hours [lo, hi)
KILL_ZONES: Dict[str, List[Tuple[float, float]]] = {
    "XAUUSD": [(7.0, 10.5), (13.0, 17.0)],
    "US30":   [(8.0, 10.5), (13.5, 16.0)],
    "USDJPY": [(7.0,  9.5), (13.0, 15.5)],
    "GBPJPY": [(7.0,  9.5), (13.0, 15.5)],
    "GBPUSD": [(7.0, 12.0), (13.0, 15.5)],
}

TF_MINUTES = {"M15": 15, "H1": 60, "H4": 240, "D1": 1440}

MIN_OBS_OU    = 80
MIN_OBS_HURST = 150
MIN_OBS_A3    = 50

# Bonferroni budget
# A1: 5 inst × 4 detrend + 2 TF × 4 + 6 subgroups × 4 ≈ 60
# A2: 5 inst × 4 estimators + 4 TF × 4 + 3 years × 4 ≈ 60
# A3: 5 inst × 4 thresh × 4 lags + ACF × 5 ≈ 100 + garch ≈ 120
N_TOTAL_TESTS = 260
BONFERRONI_ALPHA = 0.05 / N_TOTAL_TESTS   # ≈ 0.000192

print(f"Output dir  : {OUT_DIR}")
print(f"Bonferroni α*: {BONFERRONI_ALPHA:.6f}  ({N_TOTAL_TESTS} tests)")

# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

class _NpEnc(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):  return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray):  return obj.tolist()
        if isinstance(obj, pd.Timestamp): return str(obj)
        return super().default(obj)

def _safe(x):
    if x is None: return None
    if isinstance(x, float) and (np.isnan(x) or np.isinf(x)): return None
    if isinstance(x, (np.integer,)):  return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    return x


def load_ohlcv(symbol: str, tf: str) -> Optional[pd.DataFrame]:
    prefix = INSTRUMENTS.get(symbol, symbol)
    path = os.path.join(DATA_DIR, f"{prefix}_{tf}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])
    df["time"] = pd.to_datetime(df["time"])
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)
    return df


def gap_mask_returns(df: pd.DataFrame, tf: str) -> np.ndarray:
    """
    Boolean mask of length n-1: True where consecutive bar pair does NOT span
    an overnight/weekend gap (gap ≤ 3× expected bar width).
    Always True for D1.
    """
    n = len(df)
    if n < 2 or tf == "D1":
        return np.ones(n - 1, dtype=bool)
    expected_min = TF_MINUTES.get(tf, 60)
    gaps_sec = df["time"].diff().dt.total_seconds().iloc[1:].values
    gaps_min = gaps_sec / 60.0
    return gaps_min <= expected_min * 3.0


def log_returns(df: pd.DataFrame, tf: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (r, valid) where r = log-returns (length n-1) and valid is
    a bool mask excluding gap-spanning transitions.
    """
    closes = df["close"].values.astype(np.float64)
    r = np.diff(np.log(np.maximum(closes, 1e-10)))
    valid = gap_mask_returns(df, tf) & np.isfinite(r)
    return r, valid


def kz_mask(df: pd.DataFrame, symbol: str) -> np.ndarray:
    """Boolean mask: True for bars inside any kill-zone window."""
    h = df["time"].dt.hour + df["time"].dt.minute / 60.0
    mask = np.zeros(len(df), dtype=bool)
    for lo, hi in KILL_ZONES.get(symbol, []):
        mask |= ((h >= lo) & (h < hi)).values
    return mask


def year_mask(df: pd.DataFrame, yr: int) -> np.ndarray:
    return (df["time"].dt.year == yr).values


# ═══════════════════════════════════════════════════════════════════════════
# A1 — ORNSTEIN-UHLENBECK HALF-LIFE
# ═══════════════════════════════════════════════════════════════════════════

def _detrend(price: np.ndarray, method: str) -> np.ndarray:
    """
    Return detrended price residuals (NaN where insufficient history).
    Methods: sma20 | sma50 | sma100 | linear_rolling
    """
    p = pd.Series(price)
    if method.startswith("sma"):
        w = int(method[3:])
        trend = p.rolling(w, min_periods=w).mean().values
    elif method == "linear_rolling":
        # 100-bar rolling linear detrend (residual at the last bar of each window)
        w = 100
        trend = np.full(len(price), np.nan)
        t = np.arange(w + 1, dtype=float)
        for i in range(w, len(price)):
            seg = price[i - w: i + 1]
            c = np.polyfit(t, seg, 1)
            trend[i] = np.polyval(c, w)   # fitted value at the last bar
    else:
        return price.copy()
    res = price - trend
    return res


def _ou_fit(x_raw: np.ndarray, gap_valid: Optional[np.ndarray] = None) -> Dict:
    """
    ADF regression: ΔX_t = α + β·X_{t-1} + ε
    HL = -ln2 / β   (β < 0 ↔ mean reversion)

    gap_valid: bool mask length n-1 masking out cross-gap transitions.
    """
    if not HAS_STATSMODELS:
        return {"error": "statsmodels not installed"}

    x = x_raw.copy()
    finite = np.isfinite(x)

    # We need to build aligned (dX, X_lag) pairs.
    # A pair (i-1, i) is valid iff both x[i-1] and x[i] are finite AND
    # the transition is not a gap.
    n = len(x)
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

    if n_obs < MIN_OBS_OU:
        return {"error": f"n_obs={n_obs} < {MIN_OBS_OU}", "n": int(n_obs)}

    try:
        X_reg = sm.add_constant(Xlag)
        res = sm.OLS(dX, X_reg).fit()
        beta = float(res.params[1])
        se   = float(res.bse[1])
        r2   = float(res.rsquared)
        t_stat = beta / max(se, 1e-12)
        p_val  = float(stats.t.sf(-t_stat, df=n_obs - 2))  # one-tailed: β < 0

        if beta >= 0:
            return {
                "half_life": None,
                "beta": _safe(beta),
                "beta_se": _safe(se),
                "r2": _safe(r2),
                "n": int(n_obs),
                "note": "beta≥0 — unit root or explosive, no mean reversion",
            }

        hl     = float(-np.log(2.0) / beta)
        # Delta method: HL = -ln2/β → dHL/dβ = ln2/β²
        se_hl  = float(np.log(2.0) / beta ** 2 * se)
        ci_lo  = float(hl - 1.96 * se_hl)
        ci_hi  = float(hl + 1.96 * se_hl)

        return {
            "half_life":     _safe(hl),
            "half_life_ci_lo": _safe(max(ci_lo, 0.0)),
            "half_life_ci_hi": _safe(ci_hi),
            "beta":          _safe(beta),
            "beta_se":       _safe(se),
            "beta_t":        _safe(t_stat),
            "beta_p":        _safe(p_val),
            "r2":            _safe(r2),
            "n":             int(n_obs),
        }
    except Exception as e:
        return {"error": str(e), "n": int(n_obs)}


def _run_ou_for_df(df: pd.DataFrame, tf: str) -> Dict:
    """Run all four detrend methods for a given OHLCV dataframe."""
    price    = df["close"].values.astype(np.float64)
    gap_ok   = gap_mask_returns(df, tf)   # length n-1
    results  = {}
    for method in ["sma20", "sma50", "sma100", "linear_rolling"]:
        detrended = _detrend(price, method)
        results[method] = _ou_fit(detrended, gap_valid=gap_ok)
    return results


def run_a1(all_results: Dict):
    print("\n" + "=" * 60)
    print("A1: ORNSTEIN-UHLENBECK HALF-LIFE")
    print("=" * 60)
    a1: Dict = {}

    # 1. All 5 instruments at H1
    for sym in INSTRUMENTS:
        df = load_ohlcv(sym, "H1")
        if df is None:
            print(f"  {sym} H1 : NO DATA")
            continue
        print(f"  {sym} H1 (n={len(df)}) ...", end=" ", flush=True)
        a1[f"{sym}_H1_All"] = _run_ou_for_df(df, "H1")
        print("done")

    # 2. XAUUSD at M15 and H4
    for tf in ["M15", "H4"]:
        df = load_ohlcv("XAUUSD", tf)
        if df is None:
            continue
        print(f"  XAUUSD {tf} (n={len(df)}) ...", end=" ", flush=True)
        a1[f"XAUUSD_{tf}_All"] = _run_ou_for_df(df, tf)
        print("done")

    # 3. XAUUSD H1 year splits
    df_h1 = load_ohlcv("XAUUSD", "H1")
    if df_h1 is not None:
        for yr in [2024, 2025, 2026]:
            df_yr = df_h1[year_mask(df_h1, yr)].reset_index(drop=True)
            if len(df_yr) < MIN_OBS_OU + 1:
                print(f"  XAUUSD H1 {yr} : insufficient data (n={len(df_yr)})")
                continue
            print(f"  XAUUSD H1 {yr} (n={len(df_yr)}) ...", end=" ", flush=True)
            a1[f"XAUUSD_H1_{yr}"] = _run_ou_for_df(df_yr, "H1")
            print("done")

        # 4. Kill-zone vs off-hours subsample
        kz = kz_mask(df_h1, "XAUUSD")
        for label, mask in [("KillZone", kz), ("OffHours", ~kz)]:
            df_sub = df_h1[mask].reset_index(drop=True)
            if len(df_sub) < MIN_OBS_OU + 1:
                continue
            print(f"  XAUUSD H1 {label} (n={len(df_sub)}) ...", end=" ", flush=True)
            a1[f"XAUUSD_H1_{label}"] = _run_ou_for_df(df_sub, "H1")
            print("done")

    all_results["A1_OU_HalfLife"] = a1


# ═══════════════════════════════════════════════════════════════════════════
# A2 — FRACTIONAL INTEGRATION / HURST EXPONENT
# ═══════════════════════════════════════════════════════════════════════════

def _gph(r: np.ndarray, bw_exp: float) -> Dict:
    """
    Geweke-Porter-Hudak (1983) log-periodogram estimator.
    Regresses log I(λ_j) on log λ_j; slope = -2d.
    """
    r = r[np.isfinite(r)]
    n = len(r)
    m = max(int(n ** bw_exp), 5)
    m = min(m, n // 4)

    fft_vals = np.fft.fft(r - np.mean(r))
    I_full = (np.abs(fft_vals) ** 2) / (2.0 * np.pi * n)

    j = np.arange(1, m + 1)
    lam = 2.0 * np.pi * j / n
    log_I   = np.log(np.maximum(I_full[j], 1e-300))
    log_lam = np.log(lam)

    valid = np.isfinite(log_I) & np.isfinite(log_lam)
    if valid.sum() < 5:
        return {"error": "too few valid frequencies", "n": int(n)}

    xv, yv = log_lam[valid], log_I[valid]
    X = np.column_stack([np.ones(len(xv)), xv])
    try:
        coef, _, _, _ = np.linalg.lstsq(X, yv, rcond=None)
        d_hat = float(-coef[1] / 2.0)

        yhat  = X @ coef
        resid = yv - yhat
        dof   = max(len(yv) - 2, 1)
        s2    = float(np.sum(resid ** 2) / dof)
        XtX_i = np.linalg.inv(X.T @ X)
        se_d  = float(np.sqrt(max(s2 * XtX_i[1, 1], 0.0)) / 2.0)

        t_val = d_hat / max(se_d, 1e-12)
        p_val = float(2.0 * stats.t.sf(abs(t_val), df=dof))

        return {
            "d": _safe(d_hat),
            "d_se": _safe(se_d),
            "d_ci_lo": _safe(d_hat - 1.96 * se_d),
            "d_ci_hi": _safe(d_hat + 1.96 * se_d),
            "t_stat":  _safe(t_val),
            "p_value": _safe(p_val),
            "n": int(n), "m": int(m),
            "bandwidth_exp": float(bw_exp),
        }
    except np.linalg.LinAlgError:
        return {"error": "singular matrix", "n": int(n)}


def _whittle(r: np.ndarray) -> Dict:
    """
    Whittle (1951) approximate MLE for ARFIMA(0,d,0).
    Profile likelihood: W(d) = log(σ̂²(d)) + mean(log g(λ_j; d))
    where g(λ; d) = (2 sin(λ/2))^{-2d}
    """
    r = r[np.isfinite(r)]
    n = len(r)
    m = n // 2

    fft_vals = np.fft.fft(r - np.mean(r))
    I_j = (np.abs(fft_vals[1: m + 1]) ** 2) / (2.0 * np.pi * n)

    j   = np.arange(1, m + 1)
    lam = 2.0 * np.pi * j / n
    sin_half = np.maximum(np.sin(lam / 2.0), 1e-12)

    def obj(d: float) -> float:
        log_g = -2.0 * d * np.log(2.0 * sin_half)
        log_g = np.clip(log_g, -50.0, 50.0)
        g = np.exp(log_g)
        sigma2 = float(np.mean(I_j / np.maximum(g, 1e-100)))
        if sigma2 <= 0 or not np.isfinite(sigma2):
            return 1e10
        return float(np.log(sigma2) + np.mean(log_g))

    try:
        res = minimize_scalar(obj, bounds=(-0.49, 0.49), method="bounded",
                              options={"xatol": 1e-6, "maxiter": 500})
        d_hat = float(res.x)
        # Asymptotic SE: Var(d̂_Whittle) ≈ π²/(24m)
        se_d  = float(np.sqrt(np.pi ** 2 / (24.0 * m)))
        return {
            "d": _safe(d_hat),
            "d_se": _safe(se_d),
            "d_ci_lo": _safe(d_hat - 1.96 * se_d),
            "d_ci_hi": _safe(d_hat + 1.96 * se_d),
            "n": int(n),
        }
    except Exception as e:
        return {"error": str(e), "n": int(n)}


def _hurst_rs(r: np.ndarray) -> Dict:
    """Classical rescaled-range (R/S) Hurst exponent."""
    r = r[np.isfinite(r)]
    n = len(r)
    if n < MIN_OBS_HURST:
        return {"error": f"n={n} < {MIN_OBS_HURST}", "n": int(n)}

    sizes = sorted(set(max(10, n // k) for k in [2, 3, 4, 6, 8, 12, 16, 24, 32, 48]))
    log_n, log_rs = [], []
    for s in sizes:
        if s < 10 or s > n // 2:
            continue
        chunks = [r[i * s: (i + 1) * s] for i in range(n // s)]
        rs_vals = []
        for ch in chunks:
            S = float(np.std(ch, ddof=1))
            if S <= 0:
                continue
            dev = np.cumsum(ch - np.mean(ch))
            RS  = (np.max(dev) - np.min(dev)) / S
            if RS > 0:
                rs_vals.append(RS)
        if rs_vals:
            log_n.append(np.log(s))
            log_rs.append(np.log(np.mean(rs_vals)))

    if len(log_n) < 4:
        return {"error": "insufficient window sizes", "n": int(n)}

    ln_arr = np.array(log_n)
    lrs_arr = np.array(log_rs)
    coef   = np.polyfit(ln_arr, lrs_arr, 1)
    H      = float(coef[0])
    yhat   = np.polyval(coef, ln_arr)
    ss_res = float(np.sum((lrs_arr - yhat) ** 2))
    ss_tot = float(np.sum((lrs_arr - np.mean(lrs_arr)) ** 2))
    r2     = float(1.0 - ss_res / max(ss_tot, 1e-10))

    return {
        "H":       _safe(H),
        "d":       _safe(H - 0.5),
        "r2":      _safe(r2),
        "n_scales": len(log_n),
        "n":       int(n),
        "bias_warning": n < 2000,
    }


def _hurst_dfa(r: np.ndarray) -> Dict:
    """Detrended Fluctuation Analysis Hurst exponent."""
    r = r[np.isfinite(r)]
    n = len(r)
    if n < MIN_OBS_HURST:
        return {"error": f"n={n} < {MIN_OBS_HURST}", "n": int(n)}

    y = np.cumsum(r - np.mean(r))

    sizes = sorted(set(max(10, n // k) for k in [2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64]))
    log_s, log_f = [], []
    t = np.arange(0, dtype=float)   # placeholder

    for s in sizes:
        if s < 10:
            continue
        nw = n // s
        if nw < 2:
            continue
        t = np.arange(s, dtype=float)
        F_list = []
        for w in range(nw):
            seg = y[w * s: (w + 1) * s]
            coef = np.polyfit(t, seg, 1)
            resid = seg - np.polyval(coef, t)
            F_list.append(float(np.sqrt(np.mean(resid ** 2))))
        if F_list:
            log_s.append(np.log(s))
            log_f.append(np.log(np.mean(F_list) + 1e-100))

    if len(log_s) < 4:
        return {"error": "insufficient scales", "n": int(n)}

    ls_arr = np.array(log_s)
    lf_arr = np.array(log_f)
    coef   = np.polyfit(ls_arr, lf_arr, 1)
    H      = float(coef[0])
    yhat   = np.polyval(coef, ls_arr)
    ss_res = float(np.sum((lf_arr - yhat) ** 2))
    ss_tot = float(np.sum((lf_arr - np.mean(lf_arr)) ** 2))
    r2     = float(1.0 - ss_res / max(ss_tot, 1e-10))

    return {
        "H":        _safe(H),
        "d":        _safe(H - 0.5),
        "r2":       _safe(r2),
        "n_scales": len(log_s),
        "n":        int(n),
    }


def _classify_d(d: Optional[float]) -> str:
    if d is None or not np.isfinite(d):
        return "UNKNOWN"
    if d > 0.10:
        return "PERSISTENT"
    if d < -0.10:
        return "ANTI-PERSISTENT"
    return "NEUTRAL"


def _a2_for_returns(r_clean: np.ndarray, label: str) -> Dict:
    """Run all four A2 estimators on a gap-filtered, finite return series."""
    result: Dict = {"label": label, "n": int(len(r_clean))}
    result["GPH_sqrt_n"] = _gph(r_clean, 0.50)
    result["GPH_n065"]   = _gph(r_clean, 0.65)
    result["Whittle"]    = _whittle(r_clean)
    result["RS_Hurst"]   = _hurst_rs(r_clean)
    result["DFA_Hurst"]  = _hurst_dfa(r_clean)

    # Consensus d (average of GPH estimates and Whittle)
    d_est, H_est = [], []
    for k in ["GPH_sqrt_n", "GPH_n065", "Whittle"]:
        v = result[k].get("d")
        if v is not None and np.isfinite(v):
            d_est.append(v)
    for k in ["RS_Hurst", "DFA_Hurst"]:
        v = result[k].get("H")
        if v is not None and np.isfinite(v):
            H_est.append(v)

    d_mean = float(np.mean(d_est)) if d_est else None
    H_mean = float(np.mean(H_est)) if H_est else None
    result["summary"] = {
        "d_mean":            _safe(d_mean),
        "H_mean":            _safe(H_mean),
        "classification_d":  _classify_d(d_mean),
        "classification_H":  _classify_d(H_mean - 0.5 if H_mean is not None else None),
    }
    return result


def run_a2(all_results: Dict):
    print("\n" + "=" * 60)
    print("A2: FRACTIONAL INTEGRATION / HURST EXPONENT")
    print("=" * 60)
    a2: Dict = {}

    # All 5 instruments at H1
    for sym in INSTRUMENTS:
        df = load_ohlcv(sym, "H1")
        if df is None:
            continue
        r, valid = log_returns(df, "H1")
        r_clean  = r[valid]
        print(f"  {sym} H1 (n_ret={len(r_clean)}) ...", end=" ", flush=True)
        a2[f"{sym}_H1_All"] = _a2_for_returns(r_clean, f"{sym} H1 All")
        print("done")

    # XAUUSD at M15, H4, D1
    for tf in ["M15", "H4", "D1"]:
        df = load_ohlcv("XAUUSD", tf)
        if df is None:
            continue
        r, valid = log_returns(df, tf)
        r_clean  = r[valid]
        print(f"  XAUUSD {tf} (n_ret={len(r_clean)}) ...", end=" ", flush=True)
        a2[f"XAUUSD_{tf}_All"] = _a2_for_returns(r_clean, f"XAUUSD {tf} All")
        print("done")

    # XAUUSD H1 year splits
    df_h1 = load_ohlcv("XAUUSD", "H1")
    if df_h1 is not None:
        for yr in [2024, 2025, 2026]:
            df_yr = df_h1[year_mask(df_h1, yr)].reset_index(drop=True)
            if len(df_yr) < MIN_OBS_HURST + 1:
                continue
            r, valid = log_returns(df_yr, "H1")
            r_clean  = r[valid]
            if len(r_clean) < MIN_OBS_HURST:
                print(f"  XAUUSD H1 {yr} : n_ret={len(r_clean)}, too small — skipped")
                continue
            print(f"  XAUUSD H1 {yr} (n_ret={len(r_clean)}) ...", end=" ", flush=True)
            a2[f"XAUUSD_H1_{yr}"] = _a2_for_returns(r_clean, f"XAUUSD H1 {yr}")
            print("done")

    all_results["A2_Hurst_ARFIMA"] = a2


# ═══════════════════════════════════════════════════════════════════════════
# A3 — COMPRESSION-BEFORE-EXPANSION
# ═══════════════════════════════════════════════════════════════════════════

def _compute_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Wilder's ATR using exponential smoothing."""
    hi  = df["high"].values.astype(np.float64) if "high"  in df.columns else None
    lo  = df["low"].values.astype(np.float64)  if "low"   in df.columns else None
    cls = df["close"].values.astype(np.float64)
    n   = len(cls)

    if hi is None or lo is None:
        tr = np.concatenate([[0.0], np.abs(np.diff(cls))])
    else:
        prev = np.roll(cls, 1)
        prev[0] = cls[0]
        tr = np.maximum(hi - lo,
             np.maximum(np.abs(hi - prev), np.abs(lo - prev)))

    atr = np.full(n, np.nan)
    if n < period:
        return atr
    atr[period - 1] = float(np.mean(tr[:period]))
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _a3_for_df(df: pd.DataFrame, symbol: str, tf: str,
               thresholds: List[float], fwd_lags: List[int]) -> Dict:
    n = len(df)
    if n < MIN_OBS_A3 + max(fwd_lags):
        return {"error": f"n={n} too small", "n": int(n)}

    atr14     = _compute_atr(df, 14)
    atr_avg20 = pd.Series(atr14).rolling(20, min_periods=20).mean().values
    atr_ratio = np.where((atr_avg20 > 0) & np.isfinite(atr_avg20),
                         atr14 / atr_avg20, np.nan)

    # ATR autocorrelation
    atr_acf_vals = None
    valid_ratio  = atr_ratio[np.isfinite(atr_ratio)]
    if HAS_STATSMODELS and len(valid_ratio) > 40:
        try:
            acf_out = sm_acf(valid_ratio, nlags=20, fft=True, missing="drop")
            atr_acf_vals = [_safe(float(v)) for v in acf_out[1:21]]
        except Exception:
            pass

    result: Dict = {
        "symbol": symbol, "tf": tf, "n": int(n),
        "n_valid_atr_ratio": int(np.sum(np.isfinite(atr_ratio))),
        "atr_acf_lags_1_20": atr_acf_vals,
    }

    thresh_results: Dict = {}
    for thresh in thresholds:
        comp_mask   = np.isfinite(atr_ratio) & (atr_ratio < thresh)
        normal_mask = np.isfinite(atr_ratio) & (atr_ratio >= thresh)

        lag_results: Dict = {}
        for lag in fwd_lags:
            # future_atr_ratio[t] = atr_ratio[t + lag]
            future = np.full(len(atr_ratio), np.nan)
            if lag < len(atr_ratio):
                future[: len(atr_ratio) - lag] = atr_ratio[lag:]

            comp_v   = future[comp_mask   & np.isfinite(future)]
            normal_v = future[normal_mask & np.isfinite(future)]

            if len(comp_v) < 10 or len(normal_v) < 10:
                lag_results[f"lag_{lag}"] = {
                    "error": "insufficient samples",
                    "n_compressed": int(len(comp_v)),
                    "n_normal": int(len(normal_v)),
                }
                continue

            stat_gt, p_one = mannwhitneyu(comp_v, normal_v, alternative="greater")
            _, p_two       = mannwhitneyu(comp_v, normal_v, alternative="two-sided")
            mean_c  = float(np.mean(comp_v))
            mean_n  = float(np.mean(normal_v))
            exp_r   = float(mean_c / mean_n) if mean_n > 0 else None

            lag_results[f"lag_{lag}"] = {
                "n_compressed": int(len(comp_v)),
                "n_normal":     int(len(normal_v)),
                "mean_atr_comp":   _safe(mean_c),
                "mean_atr_normal": _safe(mean_n),
                "expansion_ratio": _safe(exp_r),
                "mw_stat":         _safe(float(stat_gt)),
                "p_one_sided":     _safe(float(p_one)),
                "p_two_sided":     _safe(float(p_two)),
                "sig_nominal":     bool(p_one < 0.05),
                "sig_bonferroni":  bool(p_one < BONFERRONI_ALPHA),
            }

        n_c   = int(np.sum(comp_mask))
        n_n   = int(np.sum(normal_mask))
        total = max(n_c + n_n, 1)
        thresh_results[f"thresh_{thresh}"] = {
            "threshold":      thresh,
            "n_compressed":   n_c,
            "n_normal":       n_n,
            "pct_compressed": _safe(n_c / total),
            "lags":           lag_results,
        }

    result["thresholds"] = thresh_results

    # GARCH / AR(1) comparison
    # Test whether compression dummy adds predictive power beyond AR(1) of ATR ratio.
    # A significant compression_coef means the effect is NOT fully explained by GARCH
    # persistence (which is equivalent to AR dynamics in the variance).
    if HAS_STATSMODELS and np.sum(np.isfinite(atr_ratio)) > 100:
        try:
            future1 = np.full(len(atr_ratio), np.nan)
            future1[:-1] = atr_ratio[1:]

            both_ok = np.isfinite(atr_ratio) & np.isfinite(future1)
            y_g     = future1[both_ok]
            x1_g    = atr_ratio[both_ok]
            comp_d  = (x1_g < 0.70).astype(float)   # fixed 0.70 threshold

            X_g = sm.add_constant(np.column_stack([x1_g, comp_d]))
            r_g = sm.OLS(y_g, X_g).fit()

            result["garch_ar1_comparison"] = {
                "ar1_coef":              _safe(float(r_g.params[1])),
                "compression_coef":      _safe(float(r_g.params[2])),
                "compression_pval":      _safe(float(r_g.pvalues[2])),
                "compression_sig_p05":   bool(r_g.pvalues[2] < 0.05),
                "r2":                    _safe(float(r_g.rsquared)),
                "note": ("compression_coef > 0 and sig → effect NOT fully explained "
                         "by AR(1)/GARCH persistence"),
            }
        except Exception as exc:
            result["garch_ar1_comparison"] = {"error": str(exc)}

    return result


def run_a3(all_results: Dict):
    print("\n" + "=" * 60)
    print("A3: COMPRESSION-BEFORE-EXPANSION")
    print("=" * 60)
    a3: Dict = {}

    thresholds = [0.5, 0.6, 0.7, 0.8]
    fwd_lags   = [1, 2, 4, 8]

    # H1 for all 5 instruments
    for sym in INSTRUMENTS:
        df = load_ohlcv(sym, "H1")
        if df is None:
            continue
        print(f"  {sym} H1 (n={len(df)}) ...", end=" ", flush=True)
        a3[f"{sym}_H1"] = _a3_for_df(df, sym, "H1", thresholds, fwd_lags)
        print("done")

    # XAUUSD D1 (range dynamics at the daily level)
    df_d1 = load_ohlcv("XAUUSD", "D1")
    if df_d1 is not None and "high" in df_d1.columns:
        print(f"  XAUUSD D1 (n={len(df_d1)}) ...", end=" ", flush=True)
        a3["XAUUSD_D1"] = _a3_for_df(df_d1, "XAUUSD", "D1", thresholds, [1, 2, 3, 5])
        print("done")

    all_results["A3_Compression_Expansion"] = a3


# ═══════════════════════════════════════════════════════════════════════════
# PLOTTING
# ═══════════════════════════════════════════════════════════════════════════

_SYMS   = list(INSTRUMENTS.keys())
_COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]


def _plot_a1_bars(a1: Dict):
    methods = ["sma20", "sma50", "sma100"]
    x       = np.arange(len(_SYMS))
    w       = 0.25
    fig, ax = plt.subplots(figsize=(13, 5))

    for i, (meth, col) in enumerate(zip(methods, ["#2196F3", "#4CAF50", "#FF9800"])):
        hls, err_lo, err_hi = [], [], []
        for sym in _SYMS:
            r    = a1.get(f"{sym}_H1_All", {}).get(meth, {})
            hl   = r.get("half_life")
            cilo = r.get("half_life_ci_lo")
            cihi = r.get("half_life_ci_hi")
            if hl and np.isfinite(hl) and 0 < hl < 1000:
                hls.append(hl)
                err_lo.append(max(hl - (cilo or hl), 0.0))
                err_hi.append(max((cihi or hl) - hl, 0.0))
            else:
                hls.append(0.0); err_lo.append(0.0); err_hi.append(0.0)

        ax.bar(x + i * w, hls, w, label=meth, color=col, alpha=0.8,
               yerr=[err_lo, err_hi], capsize=3, ecolor="gray", error_kw={"linewidth": 0.8})

    ax.set_xticks(x + w); ax.set_xticklabels(_SYMS)
    ax.set_ylabel("Half-Life (H1 bars)")
    ax.set_title("A1: OU Half-Life by Instrument — H1, 3 Detrend Methods")
    ax.legend(); ax.set_ylim(bottom=0)
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "mr_a1_halflife_instruments.png")
    plt.savefig(path, dpi=120); plt.close()
    print(f"  Saved: {os.path.basename(path)}")


def _plot_a1_kz(a1: Dict):
    groups = [
        ("XAUUSD_H1_All",       "All Hours"),
        ("XAUUSD_H1_KillZone",  "Kill Zone"),
        ("XAUUSD_H1_OffHours",  "Off Hours"),
        ("XAUUSD_H1_2024",      "2024"),
        ("XAUUSD_H1_2025",      "2025"),
        ("XAUUSD_H1_2026",      "2026 (partial)"),
    ]
    methods = ["sma20", "sma50", "sma100"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for ax, meth in zip(axes, methods):
        labels, hls, elo, ehi = [], [], [], []
        for key, lbl in groups:
            r  = a1.get(key, {}).get(meth, {})
            hl = r.get("half_life")
            if hl and np.isfinite(hl) and 0 < hl < 1000:
                labels.append(lbl); hls.append(hl)
                ci_lo = r.get("half_life_ci_lo", hl)
                ci_hi = r.get("half_life_ci_hi", hl)
                elo.append(max(hl - ci_lo, 0.0))
                ehi.append(max(ci_hi - hl, 0.0))
        if not labels:
            ax.set_title(f"No data ({meth})"); continue

        ax.barh(labels, hls, xerr=[elo, ehi], color="#2196F3", alpha=0.75,
                capsize=3, error_kw={"linewidth": 0.8})
        ax.set_xlabel("Half-Life (H1 bars)")
        ax.set_title(f"Detrend: {meth}")
        ax.axvline(0, color="black", linewidth=0.5)

    plt.suptitle("A1: XAUUSD H1 OU Half-Life — Subgroup Comparison", fontsize=12)
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "mr_a1_kz_year_comparison.png")
    plt.savefig(path, dpi=120); plt.close()
    print(f"  Saved: {os.path.basename(path)}")


def _plot_a2_heatmap(a2: Dict):
    estimators  = ["GPH_sqrt_n", "GPH_n065", "Whittle", "RS_Hurst", "DFA_Hurst"]
    est_labels  = ["GPH (√n)", "GPH (n⁰·⁶⁵)", "Whittle", "R/S H", "DFA H"]
    d_mat = np.full((len(_SYMS), len(estimators)), np.nan)

    for i, sym in enumerate(_SYMS):
        res = a2.get(f"{sym}_H1_All", {})
        for j, est in enumerate(estimators):
            v = res.get(est, {}).get("d")
            if v is not None and np.isfinite(v):
                d_mat[i, j] = v

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(d_mat, cmap="RdBu_r", vmin=-0.3, vmax=0.3, aspect="auto")
    ax.set_xticks(range(len(estimators))); ax.set_xticklabels(est_labels, rotation=25, ha="right")
    ax.set_yticks(range(len(_SYMS)));     ax.set_yticklabels(_SYMS)
    ax.set_title("A2: Fractional d = H − 0.5 by Instrument & Estimator (H1)\n"
                 "Blue = anti-persistent (mean-reverting)  |  Red = persistent (trending)")
    plt.colorbar(im, ax=ax, label="d = H − 0.5")

    for i in range(len(_SYMS)):
        for j in range(len(estimators)):
            v = d_mat[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:+.3f}", ha="center", va="center", fontsize=8)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "mr_a2_hurst_heatmap.png")
    plt.savefig(path, dpi=120); plt.close()
    print(f"  Saved: {os.path.basename(path)}")


def _plot_a3_expansion(a3: Dict):
    thresholds = [0.5, 0.6, 0.7, 0.8]
    fig, axes  = plt.subplots(1, 4, figsize=(18, 5), sharey=True)

    for ax, thresh in zip(axes, thresholds):
        tkey = f"thresh_{thresh}"
        ers, p_vals, sig_flags, labels = [], [], [], []
        for sym in _SYMS:
            res   = a3.get(f"{sym}_H1", {})
            tres  = res.get("thresholds", {}).get(tkey, {})
            l1    = tres.get("lags", {}).get("lag_1", {})
            er    = l1.get("expansion_ratio")
            p     = l1.get("p_one_sided")
            if er is not None:
                labels.append(sym)
                ers.append(er)
                p_vals.append(p if p is not None else 1.0)
                sig_flags.append(p is not None and p < 0.05)

        colors = ["#E53935" if s else "#90CAF9" for s in sig_flags]
        bars = ax.bar(labels, ers, color=colors, alpha=0.85)
        ax.axhline(1.0, color="black", linewidth=1.2, linestyle="--")
        ax.set_title(f"ATR < {thresh} × avg")
        ax.set_xlabel("Instrument")
        if ax == axes[0]:
            ax.set_ylabel("Future ATR ratio (lag+1)\ncompressed / normal")

        for bar, pv in zip(bars, p_vals):
            if pv < 0.05:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.005, "*",
                        ha="center", va="bottom", fontsize=14, color="black")

    plt.suptitle("A3: Compression → Expansion (Lag +1 H1 bar)\n"
                 "Red/bold = p<0.05  |  * marks above bars  |  dashed = no effect", fontsize=11)
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "mr_a3_compression_expansion.png")
    plt.savefig(path, dpi=120); plt.close()
    print(f"  Saved: {os.path.basename(path)}")


def _plot_a3_atr_acf(a3: Dict):
    fig, ax = plt.subplots(figsize=(11, 5))
    lags = list(range(1, 21))
    n_avg = 6000
    ci_band = 1.96 / np.sqrt(n_avg)

    for sym, col in zip(_SYMS, _COLORS):
        vals = a3.get(f"{sym}_H1", {}).get("atr_acf_lags_1_20")
        if vals:
            ax.plot(lags, vals, "o-", color=col, label=sym, alpha=0.8, linewidth=1.5, markersize=4)

    ax.axhline(ci_band,  color="gray", linewidth=0.8, linestyle="--", label=f"±95% CI (~n=6000)")
    ax.axhline(-ci_band, color="gray", linewidth=0.8, linestyle="--")
    ax.axhline(0,        color="black", linewidth=0.5)
    ax.set_xlabel("Lag (H1 bars)")
    ax.set_ylabel("ACF of ATR/ATR_20avg")
    ax.set_title("A3: ATR Autocorrelation — Volatility Clustering (H1)")
    ax.legend(fontsize=9)
    ax.set_xticks(lags)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "mr_a3_atr_autocorrelation.png")
    plt.savefig(path, dpi=120); plt.close()
    print(f"  Saved: {os.path.basename(path)}")


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY MARKDOWN
# ═══════════════════════════════════════════════════════════════════════════

def _hl_str(r: Dict) -> str:
    hl = r.get("half_life")
    if hl is None or not np.isfinite(hl):
        return r.get("note", "unit root") or "—"
    ci_lo = r.get("half_life_ci_lo")
    ci_hi = r.get("half_life_ci_hi")
    if ci_lo is not None and ci_hi is not None:
        return f"{hl:.1f} [{ci_lo:.1f}–{ci_hi:.1f}]"
    return f"{hl:.1f}"


def _d_str(res: Dict, key: str) -> str:
    v = res.get(key, {}).get("d")
    if v is None or not np.isfinite(v):
        return "—"
    return f"{v:+.3f}"


def _H_str(res: Dict, key: str) -> str:
    v = res.get(key, {}).get("H")
    if v is None or not np.isfinite(v):
        return "—"
    return f"{v:.3f}"


def build_summary(all_results: Dict) -> str:
    L: List[str] = []

    def ln(s: str = ""):  L.append(s)

    ln("# GTOS Mean-Reversion Mechanics Analysis")
    ln(f"*Generated {TIMESTAMP} UTC*")
    ln(f"*Bonferroni α\\* = {BONFERRONI_ALPHA:.6f} ({N_TOTAL_TESTS} total hypothesis tests)*")
    ln()

    # ── A1 ────────────────────────────────────────────────────────────────
    a1 = all_results.get("A1_OU_HalfLife", {})
    ln("## A1: Ornstein-Uhlenbeck Half-Life")
    ln()
    ln("**Interpretation:** HL = N H1 bars means price reverts halfway to fair value in N bars.")
    ln("Trailing stop timeout recommendation: ~1.5 × HL bars after entry.")
    ln()

    ln("### All 5 Instruments — H1, SMA50 Detrend")
    ln()
    ln("| Instrument | Half-Life (bars) | 95% CI | β p-value | Mean Reversion? |")
    ln("|------------|-----------------|--------|-----------|-----------------|")
    for sym in _SYMS:
        r  = a1.get(f"{sym}_H1_All", {}).get("sma50", {})
        hl = r.get("half_life")
        p  = r.get("beta_p")
        p_s = f"{p:.4f}" if p is not None else "—"
        mr  = "YES" if (hl and np.isfinite(hl) and p is not None and p < 0.05) else \
              ("unit root" if hl is None else "weak")
        ln(f"| {sym} | {_hl_str(r)} | — | {p_s} | {mr} |")
    ln()

    ln("### XAUUSD — Timeframe Comparison (SMA50)")
    ln()
    ln("| TF | HL (bars) | HL (hours) | β p-value |")
    ln("|----|----------|------------|-----------|")
    for tf, mins in [("M15", 15), ("H1", 60), ("H4", 240)]:
        key = f"XAUUSD_{tf}_All"
        r   = a1.get(key, {}).get("sma50", {})
        hl  = r.get("half_life")
        p   = r.get("beta_p")
        if hl and np.isfinite(hl):
            hl_h = hl * mins / 60.0
            p_s = f"{p:.4f}" if p is not None else "—"
            ln(f"| {tf} | {hl:.1f} | {hl_h:.1f}h | {p_s} |")
        else:
            ln(f"| {tf} | unit root | — | — |")
    ln()

    ln("### XAUUSD H1 — Subgroup Comparison (SMA50)")
    ln()
    ln("| Subgroup | Half-Life (bars) | β p-value |")
    ln("|----------|-----------------|-----------|")
    for key, lbl in [
        ("XAUUSD_H1_All",      "All Hours"),
        ("XAUUSD_H1_KillZone", "Kill Zone only"),
        ("XAUUSD_H1_OffHours", "Off Hours"),
        ("XAUUSD_H1_2024",     "2024"),
        ("XAUUSD_H1_2025",     "2025"),
        ("XAUUSD_H1_2026",     "2026 (partial)"),
    ]:
        r  = a1.get(key, {}).get("sma50", {})
        p  = r.get("beta_p")
        p_s = f"{p:.4f}" if p is not None else "—"
        ln(f"| {lbl} | {_hl_str(r)} | {p_s} |")
    ln()

    # ── A2 ────────────────────────────────────────────────────────────────
    a2 = all_results.get("A2_Hurst_ARFIMA", {})
    ln("## A2: Fractional Integration / Hurst Exponent")
    ln()
    ln("**d = H − 0.5:**  d > 0 → persistent (trending)  |  d ≈ 0 → random walk  |  d < 0 → anti-persistent")
    ln()

    ln("### All 5 Instruments — H1")
    ln()
    ln("| Instrument | GPH (√n) d | GPH (n⁰·⁶⁵) d | Whittle d | R/S H | DFA H | Class. |")
    ln("|------------|-----------|----------------|-----------|-------|-------|--------|")
    for sym in _SYMS:
        res = a2.get(f"{sym}_H1_All", {})
        cls = res.get("summary", {}).get("classification_d", "—")
        ln(f"| {sym} | {_d_str(res,'GPH_sqrt_n')} | {_d_str(res,'GPH_n065')} | "
           f"{_d_str(res,'Whittle')} | {_H_str(res,'RS_Hurst')} | {_H_str(res,'DFA_Hurst')} | {cls} |")
    ln()

    ln("### XAUUSD — Timeframe Comparison")
    ln()
    ln("| TF | GPH (√n) d | Whittle d | R/S H | DFA H | Class. |")
    ln("|----|-----------|-----------|-------|-------|--------|")
    for tf in ["M15", "H1", "H4", "D1"]:
        key = f"XAUUSD_{tf}_All"
        res = a2.get(key, {})
        if not res:
            ln(f"| {tf} | — | — | — | — | NO DATA |")
            continue
        cls = res.get("summary", {}).get("classification_d", "—")
        ln(f"| {tf} | {_d_str(res,'GPH_sqrt_n')} | {_d_str(res,'Whittle')} | "
           f"{_H_str(res,'RS_Hurst')} | {_H_str(res,'DFA_Hurst')} | {cls} |")
    ln()

    ln("### XAUUSD H1 — Year-by-Year Stability")
    ln()
    ln("| Year | n returns | GPH d | Whittle d | R/S H | DFA H |")
    ln("|------|-----------|-------|-----------|-------|-------|")
    for yr in [2024, 2025, 2026]:
        res = a2.get(f"XAUUSD_H1_{yr}", {})
        n_r = res.get("n", "—")
        if not res:
            ln(f"| {yr} | — | — | — | — | — |"); continue
        ln(f"| {yr} | {n_r} | {_d_str(res,'GPH_sqrt_n')} | {_d_str(res,'Whittle')} | "
           f"{_H_str(res,'RS_Hurst')} | {_H_str(res,'DFA_Hurst')} |")
    ln()

    # ── A3 ────────────────────────────────────────────────────────────────
    a3 = all_results.get("A3_Compression_Expansion", {})
    ln("## A3: Compression-Before-Expansion")
    ln()
    ln(f"**Expansion ratio** = mean(ATR_ratio after compressed) / mean(ATR_ratio after normal).")
    ln(f"Ratio > 1 → compression predicts expansion.")
    ln(f"\\* = p<0.05 nominal  |  \\*\\* = p < Bonferroni α\\* = {BONFERRONI_ALPHA:.5f}")
    ln()

    ln("### XAUUSD H1 — All Thresholds, Lag +1 Bar")
    ln()
    ln("| Threshold | N comp | N normal | Expansion Ratio | p (1-sided) | Sig |")
    ln("|-----------|--------|----------|-----------------|-------------|-----|")
    res_xau = a3.get("XAUUSD_H1", {})
    for thresh in [0.5, 0.6, 0.7, 0.8]:
        tres = res_xau.get("thresholds", {}).get(f"thresh_{thresh}", {})
        l1   = tres.get("lags", {}).get("lag_1", {})
        er   = l1.get("expansion_ratio")
        p    = l1.get("p_one_sided")
        nc   = tres.get("n_compressed", "—")
        nn   = tres.get("n_normal", "—")
        er_s = f"{er:.3f}" if er is not None else "—"
        p_s  = f"{p:.4f}" if p is not None else "—"
        sig  = "**" if (p and p < BONFERRONI_ALPHA) else ("*" if (p and p < 0.05) else "")
        ln(f"| {thresh} | {nc} | {nn} | {er_s} | {p_s} | {sig} |")
    ln()

    ln("### All Instruments H1 — Threshold 0.7, Lags 1 / 2 / 4 / 8")
    ln()
    ln("| Instrument | Lag 1 | Lag 2 | Lag 4 | Lag 8 |")
    ln("|------------|-------|-------|-------|-------|")
    for sym in _SYMS:
        res_s = a3.get(f"{sym}_H1", {})
        tres  = res_s.get("thresholds", {}).get("thresh_0.7", {})
        row   = [sym]
        for lag in [1, 2, 4, 8]:
            l = tres.get("lags", {}).get(f"lag_{lag}", {})
            er = l.get("expansion_ratio")
            p  = l.get("p_one_sided")
            if er is not None:
                star = "*" if (p and p < 0.05) else ""
                row.append(f"{er:.3f}{star}")
            else:
                row.append("—")
        ln("| " + " | ".join(row) + " |")
    ln()

    ln("### GARCH / AR(1) Comparison (ATR < 70% threshold)")
    ln()
    ln("| Instrument | AR(1) coef | Compression coef | p-value | Independent of GARCH? |")
    ln("|------------|-----------|-----------------|---------|----------------------|")
    for sym in _SYMS:
        gc = a3.get(f"{sym}_H1", {}).get("garch_ar1_comparison", {})
        ar1 = gc.get("ar1_coef")
        cc  = gc.get("compression_coef")
        cp  = gc.get("compression_pval")
        sig = gc.get("compression_sig_p05")
        ar1_s = f"{ar1:.3f}" if ar1 is not None else "—"
        cc_s  = f"{cc:.4f}"  if cc  is not None else "—"
        cp_s  = f"{cp:.4f}"  if cp  is not None else "—"
        ln(f"| {sym} | {ar1_s} | {cc_s} | {cp_s} | {'YES *' if sig else 'no'} |")
    ln()

    ln("### ATR Autocorrelation Summary (first 3 lags, H1)")
    ln()
    ln("| Instrument | ACF(1) | ACF(2) | ACF(3) |")
    ln("|------------|--------|--------|--------|")
    for sym in _SYMS:
        acf_v = a3.get(f"{sym}_H1", {}).get("atr_acf_lags_1_20")
        if acf_v and len(acf_v) >= 3:
            ln(f"| {sym} | {acf_v[0]:.3f} | {acf_v[1]:.3f} | {acf_v[2]:.3f} |")
        else:
            ln(f"| {sym} | — | — | — |")
    ln()

    # ── GTOS Implications ────────────────────────────────────────────────
    ln("## GTOS Trading Implications")
    ln()

    hl_all   = a1.get("XAUUSD_H1_All",      {}).get("sma50", {}).get("half_life")
    hl_kz    = a1.get("XAUUSD_H1_KillZone", {}).get("sma50", {}).get("half_life")

    ln("### A1 → Trailing Stop Timeout")
    if hl_all and np.isfinite(hl_all):
        ln(f"- XAUUSD H1 mean-reversion half-life (SMA50): **{hl_all:.1f} bars**")
        ln(f"  → Timeout at 1.5× HL = **{1.5*hl_all:.0f} H1 bars ≈ {1.5*hl_all:.0f}h**")
        ln(f"  → Trades still open after {1.5*hl_all:.0f} bars are fighting a dying reversion.")
    else:
        ln("- XAUUSD H1: unit root detected at SMA50 detrend — no reliable HL estimate.")

    if hl_kz and np.isfinite(hl_kz) and hl_all and np.isfinite(hl_all):
        ratio = hl_kz / hl_all
        direction = "FASTER" if ratio < 1 else "SLOWER"
        ln(f"- Kill Zone HL: {hl_kz:.1f} bars ({direction} than all-hours, ratio={ratio:.2f})")
        if ratio < 0.8:
            ln("  → **Kill zones show meaningfully faster mean reversion.**")
            ln("    This supports why OB-retest setups fire predominantly in KZ: price")
            ln("    returns to fair value faster during institutional activity.")
    ln()

    ln("### A2 → Regime Diagnosis")
    cls_xau = a2.get("XAUUSD_H1_All", {}).get("summary", {}).get("classification_d", "—")
    d_mean  = a2.get("XAUUSD_H1_All", {}).get("summary", {}).get("d_mean")
    ln(f"- XAUUSD H1 fractional d classification: **{cls_xau}**" +
       (f" (d≈{d_mean:.3f})" if d_mean is not None else ""))
    if cls_xau == "NEUTRAL":
        ln("  → Confirms VR-test result: linear momentum/reversion strategies won't extract edge.")
        ln("  → GTOS edge must be NONLINEAR (OB zone precision) — consistent with findings.")
    elif cls_xau == "ANTI-PERSISTENT":
        ln("  → Mild mean-reversion in returns. Validates the OB-retest premise at the return level.")
    elif cls_xau == "PERSISTENT":
        ln("  → Returns show trending behaviour. Trailing stops should lean towards letting")
        ln("    winners run rather than mean-reversion exits.")
    ln()

    ln("### A3 → Pre-Screen & Position Sizing")
    er_07 = res_xau.get("thresholds", {}).get("thresh_0.7", {}) \
                   .get("lags", {}).get("lag_1", {})
    er    = er_07.get("expansion_ratio")
    p     = er_07.get("p_one_sided")
    if er is not None:
        ln(f"- After XAUUSD ATR < 70% of 20-bar avg: next H1 ATR is **{er:.3f}×** normal")
        if p and p < 0.05:
            ln(f"  → Statistically significant (p={p:.4f} < 0.05).")
            ln("  → **IMPLICATION:** Narrow-range bars currently killed by pre-screen may be")
            ln("    *setup* bars — they predict next-bar volatility expansion where OB retests form.")
            ln("  → Propose to CEO: pilot 'compression alert' flag on H1 to monitor")
            ln("    whether OB setups on the NEXT bar have higher win rate.")
        else:
            ln(f"  → Not significant (p={p:.4f} ≥ 0.05). No reliable compression→expansion signal.")

    ln()
    ln("---")
    ln(f"*Plots: {PLOTS_DIR}*")

    return "\n".join(L)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("GTOS MEAN-REVERSION MECHANICS ANALYSIS")
    print("=" * 70)

    all_results: Dict = {
        "timestamp":        TIMESTAMP,
        "bonferroni_alpha": float(BONFERRONI_ALPHA),
        "n_total_tests":    N_TOTAL_TESTS,
    }

    run_a1(all_results)
    run_a2(all_results)
    run_a3(all_results)

    # Plots
    print("\nGenerating plots ...")
    try:
        _plot_a1_bars(all_results["A1_OU_HalfLife"])
        _plot_a1_kz(all_results["A1_OU_HalfLife"])
        _plot_a2_heatmap(all_results["A2_Hurst_ARFIMA"])
        _plot_a3_expansion(all_results["A3_Compression_Expansion"])
        _plot_a3_atr_acf(all_results["A3_Compression_Expansion"])
    except Exception:
        traceback.print_exc()

    # Save JSON
    json_path = os.path.join(OUT_DIR, f"mean_reversion_results_{TIMESTAMP}.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2, cls=_NpEnc)
    print(f"\nJSON  → {json_path}")

    # Save Markdown
    md      = build_summary(all_results)
    md_path = os.path.join(OUT_DIR, f"mean_reversion_summary_{TIMESTAMP}.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"MD    → {md_path}")

    print("\nDone.")
    return all_results


if __name__ == "__main__":
    main()
