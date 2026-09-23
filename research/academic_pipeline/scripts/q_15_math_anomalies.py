"""Q-15 Mathematical anomaly probes on XAUUSD (local, $0 API).

Probes:
  Q-15.4  Wavelet decomposition of H1 returns -> scale-specific predictivity.
  Q-15.6  Copula tail dependence (XAUUSD vs USDJPY and US30).
  Q-15.8  Cross-spectral coherence / frequency-domain lead-lag (XAUUSD vs USDJPY, US30).

All hypotheses PRE-REGISTERED before any data inspection (see Section 1 of
`results/Q-15_math.md`). This script is exploratory and treated as
low-probability / high-impact.

Notes
-----
- `pywt` is NOT available in this environment. Q-15.4 uses a from-scratch
  FWT implementation using Haar and Daubechies-4 filters (pyramid algorithm,
  orthonormal, periodic boundary). Cross-checked on a unit-signal sanity test.
- scipy.signal.coherence + csd used for Q-15.8; statsmodels KendallTau for Q-15.6.
- Heavy caveats: wavelet coefficients at coarser scales are heavily autocorrelated
  by construction; we report the effective sample size (ESS) alongside nominal N.
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import signal, stats


# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "historical_2026"
OUT_DIR = ROOT / "research" / "academic_pipeline" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_MD = OUT_DIR / "Q-15_math.md"
OUT_JSON = OUT_DIR / "Q-15_math.json"


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
def load_ohlc(symbol: str, tf: str) -> pd.DataFrame:
    """Load CSV, parse time, return DataFrame indexed by UTC time."""
    fname = f"{symbol}_{tf}.csv"
    path = DATA_DIR / fname
    if not path.exists():
        raise FileNotFoundError(str(path))
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=False)
    df = df.sort_values("time").drop_duplicates(subset=["time"]).set_index("time")
    return df[["open", "high", "low", "close", "volume"]]


def log_returns(close: pd.Series) -> pd.Series:
    r = np.log(close).diff().dropna()
    r.name = close.name
    return r


# ----------------------------------------------------------------------------
# Q-15.4: Wavelet decomposition (from-scratch, no pywt)
# ----------------------------------------------------------------------------
# Haar filters (orthonormal):
HAAR_LO = np.array([1.0, 1.0]) / math.sqrt(2.0)
HAAR_HI = np.array([1.0, -1.0]) / math.sqrt(2.0)
# Daubechies-4 (db4) orthonormal analysis filters (low-pass `h`):
# Source: I. Daubechies (1988), standard values.
DB4_LO = np.array([
    0.2303778133088964,
    0.7148465705529154,
    0.6308807679298587,
    -0.0279837694168599,
    -0.1870348117190931,
    0.0308413818355607,
    0.0328830116668852,
    -0.0105974017850690,
])
# High-pass via QMF: g[k] = (-1)^k * h[N-1-k]
DB4_HI = np.array([((-1) ** k) * DB4_LO[len(DB4_LO) - 1 - k] for k in range(len(DB4_LO))])


def _periodic_conv_downsample(x: np.ndarray, f: np.ndarray) -> np.ndarray:
    """Periodic-boundary convolution then down-sample by 2. Orthonormal filterbank step."""
    n = len(x)
    lf = len(f)
    # Use numpy's fast convolution via roll for periodic boundary.
    out = np.zeros(n // 2)
    for k in range(n // 2):
        acc = 0.0
        for i in range(lf):
            acc += f[i] * x[(2 * k + i) % n]
        out[k] = acc
    return out


def dwt_decompose(x: np.ndarray, wavelet: str, levels: int) -> List[np.ndarray]:
    """Pyramid-algorithm DWT. Returns list of detail coefficients d_1..d_levels,
    plus the final approximation as the last element (length = N/2**levels).

    Output order: [d1, d2, ..., dL, aL].
    """
    x = np.asarray(x, dtype=float).copy()
    if wavelet == "haar":
        lo, hi = HAAR_LO, HAAR_HI
    elif wavelet == "db4":
        lo, hi = DB4_LO, DB4_HI
    else:
        raise ValueError(wavelet)
    # Zero-pad to nearest power of 2 for clean periodic boundary at all levels.
    n = 1
    while n < len(x):
        n *= 2
    if n != len(x):
        x = np.concatenate([x, np.zeros(n - len(x))])
    details: List[np.ndarray] = []
    approx = x
    for _ in range(levels):
        if len(approx) < len(lo):
            break
        d = _periodic_conv_downsample(approx, hi)
        a = _periodic_conv_downsample(approx, lo)
        details.append(d)
        approx = a
    return details + [approx]


def _reconstruct_scale(coefs: List[np.ndarray], keep_index: int, wavelet: str) -> np.ndarray:
    """Reconstruct a time series that contains ONLY scale `keep_index` (0 = d1, 1 = d2,...).
    All other detail bands and the final approximation are zeroed.

    Uses inverse filters (reflection of the analysis filters) via periodic up-sampling.
    """
    if wavelet == "haar":
        lo, hi = HAAR_LO, HAAR_HI
    else:
        lo, hi = DB4_LO, DB4_HI
    # Reverse filters for synthesis (orthonormal => transpose = reverse).
    lo_rec = lo[::-1]
    hi_rec = hi[::-1]

    # Zero everything except target band.
    zeroed = [np.zeros_like(c) for c in coefs]
    if keep_index < len(coefs) - 1:  # a detail band
        zeroed[keep_index] = coefs[keep_index].copy()
    else:  # reconstruct approximation only
        zeroed[-1] = coefs[-1].copy()

    # Inverse pyramid.
    L = len(coefs) - 1  # number of detail levels
    approx = zeroed[-1]
    for level in range(L - 1, -1, -1):
        d = zeroed[level]
        # Up-sample (insert zeros) then periodic conv with reversed filters, sum.
        n = len(approx) * 2
        up_a = np.zeros(n)
        up_a[::2] = approx
        up_d = np.zeros(n)
        up_d[::2] = d
        out = np.zeros(n)
        lf = len(lo_rec)
        for k in range(n):
            acc = 0.0
            for i in range(lf):
                acc += lo_rec[i] * up_a[(k - i) % n] + hi_rec[i] * up_d[(k - i) % n]
            out[k] = acc
        approx = out
    return approx


def _causal_scale_features(r: np.ndarray, wavelet: str, scale: int) -> np.ndarray:
    """Strictly-causal scale feature at every time t.

    For scale s and filter F of length L_F, we build a window of length
    W = 2**s * L_F of past returns r[t - W .. t - 1] (does NOT include r[t]).
    Run full DWT to `scale` levels. Take the LAST detail coefficient at that
    scale (the most recent band activity). This coefficient is computed
    entirely from returns strictly before t, so correlating it with r[t]
    has no lookahead bias.

    Returns array feat[t] aligned with r (NaN for t < W).
    """
    if wavelet == "haar":
        L_F = len(HAAR_LO)
    else:
        L_F = len(DB4_LO)
    W = (2 ** scale) * max(L_F, 2)  # ensure enough samples
    # Round up to next power of 2 >= W for clean pyramid.
    w = 1
    while w < W:
        w *= 2
    W = w
    feat = np.full(len(r), np.nan)
    for t in range(W, len(r)):
        window = r[t - W:t]
        coefs = dwt_decompose(window, wavelet, levels=scale)
        # coefs = [d1, d2, ..., dL, aL]; detail at `scale` is index scale-1.
        dL = coefs[scale - 1]
        if len(dL) == 0:
            continue
        feat[t] = dL[-1]
    return feat


def q15_4_wavelet(h1_close: pd.Series, symbol: str) -> Dict:
    """Q-15.4 on H1 log-returns, Haar and db4 at 4 levels — STRICTLY CAUSAL.

    NOTE: The intuitive "decompose once, reconstruct band, correlate with
    next return" approach has LOOKAHEAD BIAS — the reconstructed band at
    time t is built from r[t] (and sometimes r[t+1] for Haar pairings), so
    correlating it with r[t+1] partly measures raw lag-1 autocorrelation.
    We verified this: a naive implementation yields |rho|=0.32 at Haar
    scale 1 while raw lag-1 rho is ~-0.03 — the inflation is purely
    lookahead contamination.

    The causal version (used below) computes the most-recent scale-s
    detail coefficient from a sliding window of PAST returns only, then
    correlates with r[t]. Expensive but honest.
    """
    r = log_returns(h1_close).values
    n = len(r)
    results = []
    for wav in ("haar", "db4"):
        for scale in (1, 2, 3, 4):
            feat = _causal_scale_features(r, wav, scale)
            mask = np.isfinite(feat)
            x = feat[mask]
            y = r[mask]
            if len(x) < 30:
                results.append({
                    "wavelet": wav,
                    "scale": scale,
                    "approx_period_h": 2 ** scale,
                    "n": int(len(x)),
                    "note": "insufficient data after mask",
                })
                continue
            rho, p_spear = stats.spearmanr(x, y)
            hit = float(np.mean(np.sign(x) == np.sign(y)))
            # Lag-1 autocorrelation of the causal feature itself.
            if len(x) > 3:
                ac1 = float(np.corrcoef(x[:-1], x[1:])[0, 1])
            else:
                ac1 = float("nan")
            # ESS per Bartlett for |AR1| < 1:
            if -0.9999 < ac1 < 0.9999 and (1 + ac1) > 0:
                ess = len(x) * (1 - ac1) / (1 + ac1)
            else:
                ess = float("nan")
            # ESS-adjusted p-value (conservative): approximate under H0
            # t = rho * sqrt((ess-2)/(1-rho^2)) then two-sided.
            if np.isfinite(ess) and ess > 4:
                t_stat = rho * math.sqrt(max(0.0, (ess - 2) / max(1e-12, 1 - rho * rho)))
                p_ess = 2 * (1 - stats.t.cdf(abs(t_stat), df=max(1, ess - 2)))
            else:
                p_ess = float("nan")
            results.append({
                "wavelet": wav,
                "scale": scale,
                "approx_period_h": 2 ** scale,
                "n": int(len(x)),
                "ess": None if not np.isfinite(ess) else float(ess),
                "spearman_rho": float(rho),
                "spearman_p": float(p_spear),
                "spearman_p_ess": None if not np.isfinite(p_ess) else float(p_ess),
                "hit_rate": hit,
                "ac1_feat": ac1,
            })
    # Bonferroni decision rule over 4 scales per family, same alpha as spec.
    alpha = 0.05 / 4  # 0.0125 per pre-registration
    passers = [
        row
        for row in results
        if "spearman_rho" in row
        and abs(row["spearman_rho"]) >= 0.10
        and row["spearman_p"] < alpha
        and (row.get("spearman_p_ess") is None or row["spearman_p_ess"] < alpha)
    ]
    return {
        "symbol": symbol,
        "rows": results,
        "alpha_bonf": alpha,
        "passers": passers,
        "method_note": "strictly causal — feature[t] computed from r[t-W..t-1] only, then correlated with r[t]. ESS-adjusted p reported alongside nominal p; both must pass gate.",
    }


# ----------------------------------------------------------------------------
# Q-15.6: Copula tail dependence
# ----------------------------------------------------------------------------
def _empirical_tail_dep(u: np.ndarray, v: np.ndarray, q: float) -> Tuple[float, float]:
    """Return (lambda_L(q), lambda_U(q)). q is quantile (e.g. 0.10)."""
    nL = float(np.mean((u <= q) & (v <= q)))
    lambda_L = nL / q if q > 0 else float("nan")
    nU = float(np.mean((u >= 1 - q) & (v >= 1 - q)))
    lambda_U = nU / q if q > 0 else float("nan")
    return lambda_L, lambda_U


def _pit(x: np.ndarray) -> np.ndarray:
    """Probability integral transform via empirical CDF (rank/N)."""
    ranks = stats.rankdata(x, method="average")
    return ranks / (len(ranks) + 1)


def _tail_dep_gaussian(rho: float, q: float) -> Tuple[float, float]:
    """Analytic Gaussian-copula tail dependence -> 0 as q -> 0. Here we compute
    finite-q VaR-style coefficient by simulation for fair apples-to-apples."""
    # Monte Carlo.
    rng = np.random.default_rng(20260417)
    n = 200_000
    z = rng.standard_normal((n, 2))
    L = np.array([[1.0, 0.0], [rho, math.sqrt(max(0.0, 1 - rho * rho))]])
    s = z @ L.T
    u = stats.norm.cdf(s[:, 0])
    v = stats.norm.cdf(s[:, 1])
    return _empirical_tail_dep(u, v, q)


def _tail_dep_gumbel(theta: float, q: float) -> Tuple[float, float]:
    """Gumbel copula has only upper-tail dependence 2 - 2**(1/theta)."""
    if theta <= 1.0:
        return 0.0, 0.0
    lambda_U_asymp = 2.0 - 2.0 ** (1.0 / theta)
    # Simulate to get a finite-q comparable number too.
    rng = np.random.default_rng(20260418)
    n = 200_000
    # Gumbel sampling via Marshall-Olkin: stable distribution.
    # Using standard trick: V ~ stable(1/theta, 1, cos(pi/(2*theta))**theta, 0)
    # Simpler: use archimedean inversion through exponential law.
    from scipy.stats import expon, levy_stable
    alpha = 1.0 / theta
    V = levy_stable.rvs(alpha, 1, loc=0, scale=(math.cos(math.pi / (2 * theta))) ** theta, size=n, random_state=rng)
    # Ensure positivity.
    V = np.abs(V) + 1e-12
    E1 = expon.rvs(size=n, random_state=rng)
    E2 = expon.rvs(size=n, random_state=rng)
    u = np.exp(-((E1 / V) ** (1.0 / theta)))
    v = np.exp(-((E2 / V) ** (1.0 / theta)))
    lL_emp, lU_emp = _empirical_tail_dep(u, v, q)
    return lL_emp, lU_emp  # lL should be ~0


def _kendall_to_gaussian_rho(tau: float) -> float:
    return math.sin(math.pi * tau / 2.0)


def _kendall_to_gumbel_theta(tau: float) -> float:
    # Gumbel: tau = 1 - 1/theta  => theta = 1 / (1 - tau).  Only valid tau >= 0.
    if tau <= 0:
        return 1.0
    return 1.0 / (1.0 - tau)


def _bootstrap_tail_dep(u: np.ndarray, v: np.ndarray, q: float, B: int, seed: int) -> Dict:
    rng = np.random.default_rng(seed)
    n = len(u)
    lLs = np.empty(B)
    lUs = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, size=n)
        lL, lU = _empirical_tail_dep(u[idx], v[idx], q)
        lLs[b] = lL
        lUs[b] = lU
    return {
        "lambda_L_mean": float(np.mean(lLs)),
        "lambda_L_ci95": [float(np.quantile(lLs, 0.025)), float(np.quantile(lLs, 0.975))],
        "lambda_U_mean": float(np.mean(lUs)),
        "lambda_U_ci95": [float(np.quantile(lUs, 0.025)), float(np.quantile(lUs, 0.975))],
    }


def q15_6_copula(xau: pd.Series, other: pd.Series, other_name: str, q: float = 0.10) -> Dict:
    """Compute empirical lambda_L/U and compare to parametric copula fits."""
    joined = pd.concat([xau, other], axis=1, join="inner").dropna()
    joined.columns = ["xau", "other"]
    rx = np.log(joined["xau"]).diff().dropna().values
    ro = np.log(joined["other"]).diff().dropna().values
    m = min(len(rx), len(ro))
    rx = rx[-m:]
    ro = ro[-m:]
    # Pearson & Kendall.
    pear = float(np.corrcoef(rx, ro)[0, 1])
    tau, tau_p = stats.kendalltau(rx, ro)
    # Gaussian-implied rho from tau:
    rho_from_tau = _kendall_to_gaussian_rho(float(tau))
    # Empirical copula pseudo-obs.
    u = _pit(rx)
    v = _pit(ro)
    lL_emp, lU_emp = _empirical_tail_dep(u, v, q)
    # Gaussian copula with matched rho (use Kendall-derived for robustness):
    lL_gauss, lU_gauss = _tail_dep_gaussian(rho_from_tau, q)
    # Gumbel (upper tail); for lower tail compare to rotated Gumbel (theta built from abs tau).
    theta_gum = _kendall_to_gumbel_theta(float(tau))
    lL_gum, lU_gum = _tail_dep_gumbel(theta_gum, q)
    # Bootstrap CIs on empirical lambdas.
    boot = _bootstrap_tail_dep(u, v, q=q, B=2000, seed=20260417)
    # Decision rule: empirical >= 2x Gaussian AND bootstrap CI lower bound > Gaussian value.
    L_gate = (lL_emp >= 2 * lL_gauss) and (boot["lambda_L_ci95"][0] > lL_gauss)
    U_gate = (lU_emp >= 2 * lU_gauss) and (boot["lambda_U_ci95"][0] > lU_gauss)
    return {
        "other": other_name,
        "n": int(m),
        "q": q,
        "pearson": pear,
        "kendall_tau": float(tau),
        "kendall_p": float(tau_p),
        "rho_from_tau": float(rho_from_tau),
        "theta_gumbel": float(theta_gum),
        "lambda_L_empirical": float(lL_emp),
        "lambda_U_empirical": float(lU_emp),
        "lambda_L_gaussian": float(lL_gauss),
        "lambda_U_gaussian": float(lU_gauss),
        "lambda_L_gumbel": float(lL_gum),
        "lambda_U_gumbel": float(lU_gum),
        "bootstrap": boot,
        "gate_lower": bool(L_gate),
        "gate_upper": bool(U_gate),
    }


# ----------------------------------------------------------------------------
# Q-15.8: Cross-spectral coherence / frequency-domain lead-lag
# ----------------------------------------------------------------------------
def q15_8_coherence(xau: pd.Series, other: pd.Series, other_name: str) -> Dict:
    """Coherence + phase between XAUUSD and other, H1 returns."""
    joined = pd.concat([xau, other], axis=1, join="inner").dropna()
    joined.columns = ["xau", "other"]
    rx = np.log(joined["xau"]).diff().dropna().values
    ro = np.log(joined["other"]).diff().dropna().values
    m = min(len(rx), len(ro))
    rx = rx[-m:]
    ro = ro[-m:]
    # Welch with segment length ~256 (11d of H1), 50% overlap.
    nperseg = min(256, max(64, m // 8))
    f, Cxy = signal.coherence(rx, ro, fs=1.0, nperseg=nperseg)  # fs in cycles/candle
    f2, Pxy = signal.csd(rx, ro, fs=1.0, nperseg=nperseg)
    # Phase, in radians, positive means XAU leads other at that freq.
    # scipy.signal.csd computes cross-spectrum S_xy = FFT(x)*conj(FFT(y)) averaged.
    # angle(Pxy) > 0 means x leads y; convert to candles via -angle/(2 pi f).
    phase = np.angle(Pxy)
    # Avoid f=0.
    period_candles = np.where(f2 > 0, 1.0 / f2, np.inf)
    lag_candles = np.where(f2 > 0, -phase / (2 * math.pi * f2), 0.0)
    # Identify bands with coherence >= 0.5 and |lag| >= 1 candle.
    bands = []
    for i in range(len(f)):
        if Cxy[i] >= 0.5 and abs(lag_candles[i]) >= 1.0:
            bands.append({
                "freq_cycles_per_h": float(f[i]),
                "period_hours": float(period_candles[i]),
                "coherence": float(Cxy[i]),
                "phase_rad": float(phase[i]),
                "lag_hours": float(lag_candles[i]),
            })
    # Top coherence bands regardless of lag, for context.
    order = np.argsort(-Cxy)
    top = []
    for i in order[:8]:
        top.append({
            "freq_cycles_per_h": float(f[i]),
            "period_hours": float(period_candles[i]) if f[i] > 0 else None,
            "coherence": float(Cxy[i]),
            "lag_hours": float(lag_candles[i]) if f[i] > 0 else 0.0,
        })
    return {
        "other": other_name,
        "n": int(m),
        "nperseg": int(nperseg),
        "max_coherence": float(np.nanmax(Cxy)),
        "bands_passing_gate": bands,
        "top_coherence_bands": top,
    }


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------
def main() -> None:
    out: Dict = {
        "generator": "q_15_math_anomalies.py",
        "status": "PRE-REGISTERED — hypotheses in Section 1 of Q-15_math.md",
    }

    # ---- Data ----
    xau_h1 = load_ohlc("XAUUSD", "H1")
    usdjpy_h1 = load_ohlc("USDJPY", "H1")
    us30_h1 = load_ohlc("US30_cash", "H1")
    out["data"] = {
        "xau_h1_rows": int(len(xau_h1)),
        "xau_h1_first": str(xau_h1.index.min()),
        "xau_h1_last": str(xau_h1.index.max()),
        "usdjpy_h1_rows": int(len(usdjpy_h1)),
        "us30_h1_rows": int(len(us30_h1)),
    }

    # ---- Q-15.4 ----
    q15_4 = q15_4_wavelet(xau_h1["close"], "XAUUSD")
    out["q15_4"] = q15_4

    # ---- Q-15.6 ----
    q15_6_usdjpy = q15_6_copula(xau_h1["close"], usdjpy_h1["close"], "USDJPY")
    q15_6_us30 = q15_6_copula(xau_h1["close"], us30_h1["close"], "US30")
    out["q15_6"] = {"usdjpy": q15_6_usdjpy, "us30": q15_6_us30}

    # ---- Q-15.8 ----
    q15_8_usdjpy = q15_8_coherence(xau_h1["close"], usdjpy_h1["close"], "USDJPY")
    q15_8_us30 = q15_8_coherence(xau_h1["close"], us30_h1["close"], "US30")
    out["q15_8"] = {"usdjpy": q15_8_usdjpy, "us30": q15_8_us30}

    with open(OUT_JSON, "w") as fh:
        json.dump(out, fh, indent=2, default=str)

    # Markdown report.
    write_report(out)


def fmt_p(p: float) -> str:
    return f"{p:.4f}" if p >= 1e-4 else f"{p:.2e}"


def write_report(out: Dict) -> None:
    lines: List[str] = []
    lines.append("# Q-15 Mathematical Anomaly Probes on XAUUSD")
    lines.append("")
    lines.append("**Status:** PRE-REGISTERED (hypotheses written before any data inspection).  ")
    lines.append("**Date:** 2026-04-17  ")
    lines.append("**Analyst:** GTOS Research Agent (Wave 3, $0 local).  ")
    lines.append("**Script:** `research/academic_pipeline/scripts/q_15_math_anomalies.py`.  ")
    lines.append("**Data:** `data/historical_2026/XAUUSD_H1.csv`, `USDJPY_H1.csv`, `US30_cash_H1.csv` (Jan 2 – Apr 10 2026).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Hypotheses (PRE-REGISTERED)")
    lines.append("")
    lines.append("These are mathematical-anomaly probes — low probability, high impact if any pass.")
    lines.append("Heavy caveats expected.")
    lines.append("")
    lines.append("### Q-15.4 Wavelet decomposition — predictive scale components")
    lines.append("")
    lines.append("**H0:** DWT coefficients of XAUUSD H1 log-returns at scales 2/4/8/16 hours contain no information about the next-hour raw return sign beyond random (Spearman rho at lag 1 is zero).  ")
    lines.append("**H1:** At least one (wavelet, scale) pair in {Haar, db4} x {scale 1..4} has |Spearman rho| >= 0.10 with next-hour return AND Bonferroni-corrected p < 0.0125 (4 scales per family).  ")
    lines.append("**Directional prior:** I expect to fail. H1 FX/metal returns are near-efficient; most predictive structure at H1 is volatility, not return sign. If anything survives it will be scale 2 or 3 (4–8h bands, intraday session effects). Scale 4 (16h) is too close to diurnal cycles to be tradeable.  ")
    lines.append("**Effective sample size:** scale-L coefficients are decimated by 2**L and carry AR-1 by construction; we report ESS alongside nominal N.  ")
    lines.append("**Robustness requirement:** no finding is credible unless it survives the analogue test on the db4 filterbank after passing Haar (or vice versa). Single-wavelet-family findings are filed as NOT USABLE.")
    lines.append("")
    lines.append("### Q-15.6 Copula tail dependence (XAUUSD vs USDJPY, XAUUSD vs US30)")
    lines.append("")
    lines.append("**H0:** Joint tail probabilities (both assets simultaneously in their 10% tails) are consistent with a Gaussian copula calibrated from Kendall's tau.  ")
    lines.append("**H1:** Empirical lambda_L and/or lambda_U >= 2 x the Gaussian-copula-implied value AND the bootstrap 95% CI lower bound exceeds the Gaussian value.  ")
    lines.append("**Directional prior:** USDJPY vs XAUUSD should show upper tail dependence (dollar-strength risk-on events where USDJPY spikes while gold dumps — BUT those are OPPOSITE-sign co-tails, not joint-upper). Used raw log-returns; if tail dependence is lopsided it will show asymmetrically. US30 vs XAUUSD: expect weak in normal regimes, elevated in stress.  ")
    lines.append("**Caveat:** 10% quantile on n≈1600 bars = 160 joint observations, not many. CIs will be wide.")
    lines.append("")
    lines.append("### Q-15.8 Cross-spectral coherence / phase-lag lead-lag")
    lines.append("")
    lines.append("**H0:** Cross-spectral coherence between XAUUSD and USDJPY / US30 H1 returns is below 0.5 at all frequencies, OR wherever it is above 0.5, phase lag corresponds to < 1 candle.  ")
    lines.append("**H1:** At least one frequency band has coherence >= 0.5 AND phase lag corresponding to >= 1 candle in absolute value.  ")
    lines.append("**Directional prior:** Strong expectation of FAIL. Broker-feed H1 bars aggregate intra-hour flow — lead-lag at H1 is almost always << 1 hour. Any |lag| >= 1 hour with high coherence is either a rare regime marker or an artifact (boundary effects, Welch segment leakage).")
    lines.append("")
    lines.append("### Decision rules (single-line summary)")
    lines.append("")
    lines.append("| Q | Threshold |")
    lines.append("|---|---|")
    lines.append("| Q-15.4 | any (wavelet, scale) with |rho| >= 0.10 and Bonferroni p < 0.0125 |")
    lines.append("| Q-15.6 | empirical lambda_L or lambda_U >= 2x Gaussian AND bootstrap CI lower bound > Gaussian |")
    lines.append("| Q-15.8 | coherence >= 0.5 AND |phase lag| >= 1 candle in at least one band |")
    lines.append("")
    lines.append("*No trading / deployment recommendation is made in this file. Passes here are candidates for out-of-sample replication, not deployable signals.*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Data")
    lines.append("")
    d = out["data"]
    lines.append(f"- XAUUSD H1: {d['xau_h1_rows']} bars, {d['xau_h1_first']} .. {d['xau_h1_last']}.")
    lines.append(f"- USDJPY H1: {d['usdjpy_h1_rows']} bars (intersection with XAU via `dropna`).")
    lines.append(f"- US30 H1: {d['us30_h1_rows']} bars.")
    lines.append("")
    lines.append("**Library availability note:** `pywt` is NOT installed in this environment. Q-15.4 uses a from-scratch orthonormal pyramid DWT (Haar + db4, periodic boundary, power-of-2 zero-padding). `scipy.signal.coherence/csd` powers Q-15.8. `scipy.stats` and Monte Carlo simulation power Q-15.6. No finding here should be treated as a library-validated reference implementation — sanity-check on a second tool before acting.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ---- Q-15.4 ----
    q4 = out["q15_4"]
    lines.append("## 3. Q-15.4 — Wavelet scale predictivity")
    lines.append("")
    lines.append(f"Per-scale test: Spearman rho(sign of reconstructed scale component at t, next-bar raw return at t+1). Bonferroni alpha per wavelet family = {q4['alpha_bonf']:.4f} (0.05 / 4 scales).")
    lines.append("")
    lines.append("| Wavelet | Scale | Period≈(h) | N | ESS | AC1(feat) | Spearman rho | Nominal p | ESS-adj p | Hit-rate |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in q4["rows"]:
        if "spearman_rho" in r:
            ess = "n/a" if r["ess"] is None else f"{r['ess']:.0f}"
            p_ess = "n/a" if r.get("spearman_p_ess") is None else fmt_p(r["spearman_p_ess"])
            lines.append(
                f"| {r['wavelet']} | {r['scale']} | {r['approx_period_h']} | {r['n']} | {ess} | {r['ac1_feat']:.3f} | {r['spearman_rho']:+.4f} | {fmt_p(r['spearman_p'])} | {p_ess} | {r['hit_rate']:.3f} |"
            )
        else:
            lines.append(f"| {r['wavelet']} | {r['scale']} | {r['approx_period_h']} | n/a | n/a | n/a | n/a | n/a | n/a | ({r.get('note','')}) |")
    lines.append("")
    if q4["passers"]:
        lines.append("**Passers (pre-registered gate |rho|>=0.10 & Bonferroni p<0.0125):**")
        for p in q4["passers"]:
            lines.append(f"- {p['wavelet']} scale {p['scale']}: rho={p['spearman_rho']:+.4f}, p={fmt_p(p['spearman_p'])}, hit={p['hit_rate']:.3f}.")
        lines.append("")
        lines.append("Robustness cross-family requirement: a passer on Haar must also show |rho|>=0.05 at the corresponding db4 scale (or vice versa). If it does not, classify as NOT USABLE (filter-specific artifact).")
    else:
        lines.append("**No passers.** Classification: **FAIL** — wavelet scale decomposition does not surface tradeable next-hour return-sign predictivity at the pre-registered threshold.")
    lines.append("")
    lines.append("**Caveats & method notes:**")
    lines.append("")
    lines.append(f"- {q4.get('method_note','')}")
    lines.append("- The INITIAL (non-causal, 'decompose once and reconstruct band') version of this test yielded |rho| = 0.32 at Haar scale 1, which we verified is **pure lookahead contamination**: the reconstructed scale-1 value at time t embeds r[t] (and r[t+1] in some Haar pairings), so correlating with r[t+1] partially measures raw-return lag-1 autocorrelation. The results above use a strictly-causal sliding-window DWT that avoids this.")
    lines.append("- Sliding window size W = 2**scale * L_filter, rounded to power of 2. Only the MOST RECENT detail coefficient at the target scale is used as the predictor at each t.")
    lines.append("- ESS-adjusted p-value uses Bartlett ESS = n*(1-AC1)/(1+AC1) on the causal feature series; both nominal and ESS-adjusted p must pass Bonferroni alpha = 0.0125 for a finding to count.")
    lines.append("- Periodic boundary is applied WITHIN each window; windows are independent so there is no cross-window boundary leakage.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ---- Q-15.6 ----
    lines.append("## 4. Q-15.6 — Copula tail dependence")
    lines.append("")
    lines.append("For each pair, rank-transform XAU and partner H1 log-returns to uniforms. Estimate lambda_L(q=0.10) = P(V<=q | U<=q) and lambda_U(q=0.10) = P(V>=1-q | U>=1-q). Compare to Gaussian-copula calibrated on Kendall's tau (via simulation to keep finite-q apples-to-apples) and upper-tail Gumbel calibrated on tau. Bootstrap (B=2000) gives 95% CI on empirical.")
    lines.append("")
    for pair_key, pair_name in [("usdjpy", "XAUUSD x USDJPY"), ("us30", "XAUUSD x US30")]:
        q = out["q15_6"][pair_key]
        lines.append(f"### {pair_name}")
        lines.append("")
        lines.append(f"- N={q['n']}, Pearson rho={q['pearson']:+.4f}, Kendall tau={q['kendall_tau']:+.4f} (p={fmt_p(q['kendall_p'])}).")
        lines.append(f"- tau-implied Gaussian rho = {q['rho_from_tau']:+.4f}; tau-implied Gumbel theta = {q['theta_gumbel']:.3f}.")
        lines.append("")
        lines.append("| Quantity | Value |")
        lines.append("|---|---|")
        lines.append(f"| Empirical lambda_L(0.10) | {q['lambda_L_empirical']:.4f} |")
        lines.append(f"| Empirical lambda_U(0.10) | {q['lambda_U_empirical']:.4f} |")
        lines.append(f"| Gaussian-copula lambda_L(0.10) (MC) | {q['lambda_L_gaussian']:.4f} |")
        lines.append(f"| Gaussian-copula lambda_U(0.10) (MC) | {q['lambda_U_gaussian']:.4f} |")
        lines.append(f"| Gumbel-copula lambda_U(0.10) (MC) | {q['lambda_U_gumbel']:.4f} |")
        lines.append(f"| Bootstrap 95% CI for lambda_L | [{q['bootstrap']['lambda_L_ci95'][0]:.4f}, {q['bootstrap']['lambda_L_ci95'][1]:.4f}] |")
        lines.append(f"| Bootstrap 95% CI for lambda_U | [{q['bootstrap']['lambda_U_ci95'][0]:.4f}, {q['bootstrap']['lambda_U_ci95'][1]:.4f}] |")
        lines.append(f"| Gate (lower) | {'PASS' if q['gate_lower'] else 'fail'} |")
        lines.append(f"| Gate (upper) | {'PASS' if q['gate_upper'] else 'fail'} |")
        lines.append("")
    lines.append("**Caveats:**")
    lines.append("- Effective sample for joint-tail is ~n*q = ~160 events — bootstrap CIs are wide.")
    lines.append("- USDJPY vs XAUUSD often co-move via the *dollar channel*: when dollar spikes, USDJPY spikes and XAUUSD drops. That appears as tail dependence between *opposite-sign* tails, i.e. lambda_U between USDJPY returns and (-XAUUSD) returns, not lambda_U between XAUUSD and USDJPY directly. If raw-sign test shows weak upper-tail dependence, run the sign-flipped test manually before concluding no dependence.")
    lines.append("- Copula-implied Gaussian values are computed via Monte Carlo at the SAME q, not the asymptotic q->0 limit (which is 0 for Gaussian). This gives a fair finite-q comparison.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ---- Q-15.8 ----
    lines.append("## 5. Q-15.8 — Cross-spectral coherence / phase-lag")
    lines.append("")
    lines.append("Welch's method (default Hann window), 50% overlap, `nperseg` chosen per pair for stability. Coherence Cxy(f) in [0,1]; phase(Pxy(f)) from cross-spectrum; time-domain lag = -phase / (2 pi f), positive => XAU leads partner.")
    lines.append("")
    for pair_key, pair_name in [("usdjpy", "XAUUSD vs USDJPY"), ("us30", "XAUUSD vs US30")]:
        q = out["q15_8"][pair_key]
        lines.append(f"### {pair_name}")
        lines.append("")
        lines.append(f"- N={q['n']}, nperseg={q['nperseg']}, peak coherence = {q['max_coherence']:.3f}.")
        lines.append("")
        if q["bands_passing_gate"]:
            lines.append("**Bands passing gate (coherence>=0.5 AND |lag|>=1h):**")
            lines.append("")
            lines.append("| Freq (1/h) | Period (h) | Coherence | Phase (rad) | Lag (h) |")
            lines.append("|---|---|---|---|---|")
            for b in q["bands_passing_gate"]:
                lines.append(f"| {b['freq_cycles_per_h']:.4f} | {b['period_hours']:.2f} | {b['coherence']:.3f} | {b['phase_rad']:+.3f} | {b['lag_hours']:+.2f} |")
        else:
            lines.append("**No bands pass the gate.** Classification: **FAIL** for this pair.")
        lines.append("")
        lines.append("Top-8 coherence bands (for context, regardless of lag gate):")
        lines.append("")
        lines.append("| Freq (1/h) | Period (h) | Coherence | Lag (h) |")
        lines.append("|---|---|---|---|")
        for b in q["top_coherence_bands"]:
            per = "inf" if b["period_hours"] is None else f"{b['period_hours']:.2f}"
            lines.append(f"| {b['freq_cycles_per_h']:.4f} | {per} | {b['coherence']:.3f} | {b['lag_hours']:+.2f} |")
        lines.append("")
    lines.append("**Caveats:**")
    lines.append("- `nperseg` selection trades frequency resolution vs statistical stability. With ~1600 bars we get ~6 independent windows at nperseg=256; single-band coherence estimates are noisy (effective d.o.f. ≈ 12).")
    lines.append("- A coherence of 0.5 in a single band is ~2-sigma for this d.o.f.; it is NOT surprise-level. Joint requirement (coherence>=0.5 AND |lag|>=1h) raises the bar substantially.")
    lines.append("- Phase at low frequencies (long periods) is poorly estimated; lag of many candles at a long-period band is usually not economically meaningful.")
    lines.append("- Broker feeds are synchronized to GMT via MT5 server time — sub-hour lead-lag cannot be resolved at H1 sampling, by Nyquist.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ---- Summary ----
    lines.append("## 6. Overall classification")
    lines.append("")
    q4_pass = len(out["q15_4"]["passers"]) > 0
    q6_usdjpy = out["q15_6"]["usdjpy"]
    q6_us30 = out["q15_6"]["us30"]
    q6_pass = q6_usdjpy["gate_lower"] or q6_usdjpy["gate_upper"] or q6_us30["gate_lower"] or q6_us30["gate_upper"]
    q8_usdjpy = out["q15_8"]["usdjpy"]
    q8_us30 = out["q15_8"]["us30"]
    q8_pass = bool(q8_usdjpy["bands_passing_gate"]) or bool(q8_us30["bands_passing_gate"])
    lines.append(f"- Q-15.4 wavelet: **{'PASS' if q4_pass else 'FAIL'}** at the pre-registered threshold.")
    lines.append(f"- Q-15.6 copula: **{'PASS' if q6_pass else 'FAIL'}** at the pre-registered threshold (USDJPY: L={q6_usdjpy['gate_lower']}, U={q6_usdjpy['gate_upper']}; US30: L={q6_us30['gate_lower']}, U={q6_us30['gate_upper']}).")
    lines.append(f"- Q-15.8 coherence: **{'PASS' if q8_pass else 'FAIL'}** at the pre-registered threshold.")
    lines.append("")
    lines.append("**Overall:** Mathematical-anomaly probes are exploratory; any PASS is a *candidate* for out-of-sample replication on a separate window and a different broker feed, NOT a deployable signal. No trading change is authorized by this file.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 7. Reproducibility")
    lines.append("")
    lines.append("- Script: `research/academic_pipeline/scripts/q_15_math_anomalies.py`.")
    lines.append("- JSON: `research/academic_pipeline/results/Q-15_math.json` (all numbers, including per-band coherence and bootstrap draws' statistics).")
    lines.append("- Seeds: Gaussian-MC seed=20260417, Gumbel-MC seed=20260418, bootstrap seed=20260417.")
    lines.append("- Library gaps flagged: `pywt` missing -> from-scratch Haar + db4 DWT used. `scipy.stats.levy_stable` (for Gumbel sampling) is high-variance; Gumbel numbers are a sanity check only, not the decision metric.")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
    print(f"OK -> {OUT_MD}")
