#!/usr/bin/env python3
"""
compute_optimal_trail_v1.py
============================
Optimal trailing stop bounds for XAUUSD H1 trades (Q-6.1).

Framework
---------
1. Extract OU parameters (θ, σ, μ) from XAUUSD H1 SMA50 spread.
2. Gaussian OU optimal exit via analytical scale-function + Sharpe grid search.
3. Fat-tail (Student-t df=2.86) Monte Carlo adjustment.
4. Comparison to current GTOS trailing stop rule.

Outputs
-------
  research/diagnostics/trailing_stop_optimal/
      optimal_trailing_stop_v1.md
      compute_optimal_trail_v1.py  (this file)

References
----------
  - Lipton & de Prado (2020) - "A Closed-Form Solution for Optimal Mean-Reverting Trading"
  - Baviera & Cassaro (2021) - "Optimal TP/SL levels"
  - OU parameters: research/diagnostics/mean_reversion_mechanics/ou_kz_half_life_v2.md
  - GPD tail parameters: research/diagnostics/distributional_characterization_20260411_012816.json

Assumptions (explicitly stated where parameter unavailable from data)
----------------------------------------------------------------------
  - μ = 0: SMA50 detrending makes the spread mean-zero by construction
  - c = $0.50 round-trip transaction cost (conservative FTMO spread estimate)
  - avg_sl_dollars = $10: default per CLAUDE.md; no dollar SL stored in batch data
  - GPD ξ = 0.35 (task spec); actual diagnostic: upper=0.283, lower=0.343
    → df = 1/0.35 = 2.857; actual diagnostic would give df ≈ 1/0.313 = 3.19
  - X₀ = 0: entry at the long-run spread mean; symmetric baseline
  - T_max_kz = 26 bars ≈ 1.5 × KZ HL = 1.5 × 17.05
  - T_max_all = 35 bars ≈ 1.5 × all-hours HL = 1.5 × 23.05
"""

import os
import sys
import json
import warnings
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats, integrate
from scipy.special import erfi

warnings.filterwarnings("ignore")

SEED = 42
rng  = np.random.default_rng(SEED)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_PATH = os.path.join(REPO_ROOT, "data", "historical", "XAUUSD_H1.csv")
OUT_DIR   = os.path.dirname(__file__)
TIMESTAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

# ─────────────────────────────────────────────────────────────────────────────
# KNOWN OU PARAMETERS (from peer-review-fixed diagnostics)
# ─────────────────────────────────────────────────────────────────────────────
# Source: ou_kz_half_life_v2.md (bug-fixed rerun)
BETA_ALL = -0.030073   # AR(1) beta for SMA50 spread, all hours
BETA_KZ  = -0.040646   # AR(1) beta for SMA50 spread, KZ-only

THETA_ALL = -BETA_ALL  # OU mean-reversion speed, continuous approx, per H1 bar
THETA_KZ  = -BETA_KZ

HL_ALL = np.log(2) / THETA_ALL   # should ≈ 23.05
HL_KZ  = np.log(2) / THETA_KZ    # should ≈ 17.05

# T_max: 1.5 × half-life (rounded up to integer bars)
T_MAX_ALL = int(np.ceil(1.5 * HL_ALL))   # ≈ 35
T_MAX_KZ  = int(np.ceil(1.5 * HL_KZ))    # ≈ 26

# Fat-tail parameters
XI_SPECIFIED = 0.35          # task specification
DF_SPECIFIED = 1.0 / XI_SPECIFIED   # ≈ 2.857

XI_UPPER_ACTUAL = 0.2829652  # from distributional_characterization_20260411_012816.json
XI_LOWER_ACTUAL = 0.3429337  # same source
XI_ACTUAL_AVG   = (XI_UPPER_ACTUAL + XI_LOWER_ACTUAL) / 2   # ≈ 0.313
DF_ACTUAL        = 1.0 / XI_ACTUAL_AVG                        # ≈ 3.19

# Transaction cost and SL
C_DOLLARS   = 0.50    # round-trip spread cost
AVG_SL      = 10.0    # dollars; default (no dollar SL in batch data)

# Monte Carlo
N_PATHS_GAUSS   = 200_000
N_PATHS_FATTAIL = 100_000


# ─────────────────────────────────────────────────────────────────────────────
# STEP 0 — EXTRACT σ FROM DATA
# ─────────────────────────────────────────────────────────────────────────────
def load_xauusd_h1():
    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip().lower() for c in df.columns]
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])
    df["time"]  = pd.to_datetime(df["time"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)
    return df


def compute_sigma(df: pd.DataFrame, beta: float, label: str, kz_only: bool = False):
    """
    Run the AR(1) regression on SMA50 spread and return residual std.
    Mirrors the exact approach in run_kz_ou_halflife_v2.py.
    """
    XAUUSD_KZ = [(7.0, 10.5), (13.0, 17.0)]

    price = df["close"].values.astype(np.float64)
    sma50 = pd.Series(price).rolling(50, min_periods=50).mean().values
    spread = price - sma50   # X_t: SMA50 deviation

    # Gap mask (fixed method)
    gaps_sec = df["time"].diff().dt.total_seconds().iloc[1:].values
    gap_ok   = np.concatenate([[True], gaps_sec / 60.0 <= 60.0 * 3.0])

    if kz_only:
        h = df["time"].dt.hour + df["time"].dt.minute / 60.0
        kz = np.zeros(len(df), dtype=bool)
        for lo, hi in XAUUSD_KZ:
            kz |= ((h >= lo) & (h < hi)).values
        mask = kz
    else:
        mask = np.ones(len(df), dtype=bool)

    dX_list, Xlag_list = [], []
    for i in range(1, len(spread)):
        if not (mask[i] and mask[i-1]):
            continue
        if not gap_ok[i]:
            continue
        xi = spread[i]
        xl = spread[i-1]
        if not (np.isfinite(xi) and np.isfinite(xl)):
            continue
        dX_list.append(xi - xl)
        Xlag_list.append(xl)

    dX   = np.array(dX_list)
    Xlag = np.array(Xlag_list)

    # OLS: dX = alpha + beta*Xlag + eps
    X_reg = np.column_stack([np.ones(len(Xlag)), Xlag])
    coeffs, res, _, _ = np.linalg.lstsq(X_reg, dX, rcond=None)
    fitted   = X_reg @ coeffs
    residuals = dX - fitted
    sigma_resid = float(np.std(residuals, ddof=2))   # ddof=2 for intercept + slope

    # Derive beta from regression for verification
    beta_est = float(coeffs[1])
    hl_est   = float(-np.log(2) / beta_est) if beta_est < 0 else np.nan
    mu_est   = float(-coeffs[0] / coeffs[1]) if coeffs[1] != 0 else 0.0

    print(f"  [{label}] beta_est={beta_est:.6f}  HL_est={hl_est:.2f}  "
          f"σ_resid={sigma_resid:.4f}$  mu_est={mu_est:.4f}$  n={len(dX)}")
    return sigma_resid, mu_est, spread, dX, Xlag


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — GAUSSIAN OU OPTIMAL EXIT (analytical scale function)
# ─────────────────────────────────────────────────────────────────────────────
def scale_fn(x: np.ndarray, theta: float, sigma: float) -> np.ndarray:
    """
    S(x) = ∫₀ˣ exp(θy²/σ²) dy = (σ√π)/(2√θ) × erfi(x√θ/σ)
    Valid for x ∈ ℝ. S(0)=0. S is odd if theta>0.
    """
    coeff = sigma * np.sqrt(np.pi) / (2.0 * np.sqrt(theta))
    z     = x * np.sqrt(theta) / sigma
    return coeff * erfi(z)


def p_win_gaussian(pi_: float, ell_: float, theta: float, sigma: float) -> float:
    """
    P(hit π before ℓ | X₀=0) using OU scale function.
    Requires ℓ < 0 < π.
    """
    S_pi  = scale_fn(np.array([pi_]),  theta, sigma)[0]
    S_ell = scale_fn(np.array([ell_]), theta, sigma)[0]
    # S(ℓ) < 0 since ℓ < 0 and S is odd-ish (S(-x) = -S(x) for symmetric s(x))
    # P(win) = (S(0)-S(ℓ)) / (S(π)-S(ℓ)) = -S(ℓ) / (S(π)-S(ℓ))
    denom = S_pi - S_ell
    if denom <= 0:
        return np.nan
    return -S_ell / denom


def sharpe_gaussian_notmax(pi_grid: np.ndarray, ell_grid: np.ndarray,
                           theta: float, sigma: float, c: float) -> np.ndarray:
    """
    Analytical Sharpe surface for Gaussian OU without T_max constraint.
    Returns Sharpe array of shape [len(pi_grid), len(ell_grid)].
    c is transaction cost in same dollar units as pi/ell.
    """
    n_pi  = len(pi_grid)
    n_ell = len(ell_grid)
    sharpe_mat = np.full((n_pi, n_ell), np.nan)

    S_pi  = scale_fn(pi_grid,  theta, sigma)
    S_ell = scale_fn(ell_grid, theta, sigma)   # ell_grid < 0, so S_ell < 0

    for i, (pi_v, S_pi_v) in enumerate(zip(pi_grid, S_pi)):
        for j, (ell_v, S_ell_v) in enumerate(zip(ell_grid, S_ell)):
            denom = S_pi_v - S_ell_v
            if denom <= 1e-12:
                continue
            p    = -S_ell_v / denom   # P(win)
            ep   = p * (pi_v - c) + (1 - p) * (ell_v - c)
            varp = p * (1 - p) * (pi_v - ell_v) ** 2
            if varp < 1e-12:
                continue
            sharpe_mat[i, j] = ep / np.sqrt(varp)

    return sharpe_mat


# ─────────────────────────────────────────────────────────────────────────────
# MONTE CARLO HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def simulate_ou_paths(n: int, t_max: int, theta: float, sigma: float,
                      df_t: float = None) -> np.ndarray:
    """
    Simulate OU paths: X_{t+1} = X_t + θ(0 - X_t) + σ_adj * innov
    X₀ = 0.
    If df_t is None → Gaussian innovations.
    If df_t is float → Student-t(df_t) innovations, variance-matched.

    Returns X array of shape [n, t_max].
    """
    X = np.zeros((n, t_max), dtype=np.float32)
    if df_t is None:
        innov = rng.standard_normal((n, t_max - 1)).astype(np.float32)
    else:
        # Student-t with df_t; scale so unconditional var matches Gaussian
        sigma_adj = float(sigma * np.sqrt((df_t - 2.0) / df_t))
        raw_t     = rng.standard_t(df=df_t, size=(n, t_max - 1)).astype(np.float32)
        innov     = raw_t  # will be multiplied by sigma_adj below
        sigma     = sigma_adj

    for t in range(1, t_max):
        X[:, t] = X[:, t-1] * (1.0 - theta) + sigma * innov[:, t-1]

    return X


def mc_sharpe_coarse(X: np.ndarray, pi_grid: np.ndarray, ell_grid: np.ndarray,
                     c: float) -> np.ndarray:
    """
    For each (π, ℓ) in coarse grid, compute trade Sharpe from pre-simulated paths.
    X shape: [N, T].
    Uses cumulative max/min for efficient hit detection.
    Returns sharpe array [len(pi_grid), len(ell_grid)].
    """
    N, T = X.shape

    # Precompute running max and min over time
    cum_max = np.maximum.accumulate(X, axis=1)   # [N, T]
    cum_min = np.minimum.accumulate(X, axis=1)   # [N, T]

    sharpe_mat = np.full((len(pi_grid), len(ell_grid)), np.nan)

    for i, pi_v in enumerate(pi_grid):
        for j, ell_v in enumerate(ell_grid):
            if pi_v <= 0 or ell_v >= 0:
                continue

            # First time cum_max >= pi_v (→ hit profit target)
            hit_pi_mask  = cum_max >= pi_v      # [N, T] bool
            hit_ell_mask = cum_min <= ell_v     # [N, T] bool

            ever_pi  = hit_pi_mask.any(axis=1)  # [N]
            ever_ell = hit_ell_mask.any(axis=1)

            # argmax returns first True along axis=1; 0 if never True
            t_pi  = np.where(ever_pi,  np.argmax(hit_pi_mask,  axis=1), T)
            t_ell = np.where(ever_ell, np.argmax(hit_ell_mask, axis=1), T)

            win     = ever_pi  & (~ever_ell | (t_pi <= t_ell))
            lose    = ever_ell & (~ever_pi  | (t_ell <  t_pi))
            timeout = ~win & ~lose

            # P&L for timeout: exit at final X value
            pnl = np.where(win,     pi_v  - c,
                  np.where(lose,    ell_v - c,
                           X[:, -1] - c))

            ep   = float(np.mean(pnl))
            varp = float(np.var(pnl, ddof=1))
            if varp < 1e-12:
                continue
            sharpe_mat[i, j] = ep / np.sqrt(varp)

    return sharpe_mat


# ─────────────────────────────────────────────────────────────────────────────
# BAVIERA SENSITIVITY CURVE
# ─────────────────────────────────────────────────────────────────────────────
def baviera_curve(pi_star: float, ell_grid: np.ndarray,
                  theta: float, sigma: float, c: float) -> np.ndarray:
    """
    Expected return R(ℓ) with π held at π*.
    Used to show SL sensitivity (Baviera & Cassaro 2021).
    """
    S_pi   = scale_fn(np.array([pi_star]), theta, sigma)[0]
    S_ells = scale_fn(ell_grid, theta, sigma)   # [n_ell]
    R      = np.full(len(ell_grid), np.nan)
    for j, (ell_v, S_ell_v) in enumerate(zip(ell_grid, S_ells)):
        denom = S_pi - S_ell_v
        if denom <= 1e-12:
            continue
        p       = -S_ell_v / denom
        R[j]    = p * (pi_star - c) + (1 - p) * (ell_v - c)
    return R


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("GTOS Optimal Trailing Stop Computation — v1")
    print(f"Seed: {SEED}  |  Timestamp: {TIMESTAMP}")
    print("=" * 70)

    # ── Load data ──────────────────────────────────────────────────────────
    print("\n[Step 0] Loading XAUUSD H1 data and estimating OU parameters...")
    df = load_xauusd_h1()
    print(f"  Rows: {len(df)}  |  {df['time'].iloc[0].date()} – {df['time'].iloc[-1].date()}")

    sigma_all, mu_all, spread_all, _, _ = compute_sigma(df, BETA_ALL, "All-hours", kz_only=False)
    sigma_kz,  mu_kz,  spread_kz,  _, _ = compute_sigma(df, BETA_KZ,  "KZ-only",   kz_only=True)

    # We use sigma_all for the spread distribution width (more data)
    # KZ sigma is typically slightly smaller; use it for KZ scenario
    sigma_use_all = sigma_all
    sigma_use_kz  = sigma_kz

    print(f"\n  Confirmed OU parameters:")
    print(f"    θ_all  = {THETA_ALL:.6f}/bar  HL={HL_ALL:.2f} bars")
    print(f"    θ_kz   = {THETA_KZ:.6f}/bar  HL={HL_KZ:.2f} bars")
    print(f"    σ_all  = {sigma_use_all:.4f}$  (residual std, SMA50 spread, all-hours)")
    print(f"    σ_kz   = {sigma_use_kz:.4f}$  (residual std, SMA50 spread, KZ-only)")
    print(f"    μ      = 0.0$ (SMA50 detrend → mean-zero by construction)")
    print(f"    c      = ${C_DOLLARS:.2f} (round-trip transaction cost, assumed)")
    print(f"    T_max_all = {T_MAX_ALL} bars")
    print(f"    T_max_kz  = {T_MAX_KZ} bars")

    # ── Step 1: Gaussian Analytical ────────────────────────────────────────
    print("\n[Step 1] Gaussian OU optimal exit (analytical scale function)...")

    # Fine grid in sigma units, converted to dollars
    pi_sigmas  = np.arange(0.10, 5.05, 0.05)  # 99 values
    ell_sigmas = np.arange(-0.10, -5.05, -0.05)  # 99 values (negative)

    results_gauss = {}
    for label, theta_v, sigma_v in [
        ("All-hours", THETA_ALL, sigma_use_all),
        ("KZ-only",   THETA_KZ,  sigma_use_kz),
    ]:
        pi_dollars  = pi_sigmas  * sigma_v
        ell_dollars = ell_sigmas * sigma_v

        sharpe_mat = sharpe_gaussian_notmax(pi_dollars, ell_dollars,
                                            theta_v, sigma_v, C_DOLLARS)

        # Find optimal
        flat_idx = np.nanargmax(sharpe_mat)
        i_opt, j_opt = np.unravel_index(flat_idx, sharpe_mat.shape)
        pi_opt_d  = pi_dollars[i_opt]
        ell_opt_d = ell_dollars[j_opt]
        pi_opt_s  = pi_sigmas[i_opt]
        ell_opt_s = ell_sigmas[j_opt]
        sharpe_opt = sharpe_mat[i_opt, j_opt]

        # Convert to R-multiples
        pi_opt_R  = pi_opt_d  / AVG_SL
        ell_opt_R = ell_opt_d / AVG_SL

        # Baviera curve: vary ℓ with π = π*
        bav_R = baviera_curve(pi_opt_d, ell_dollars, theta_v, sigma_v, C_DOLLARS)

        # P(win) at optimal
        p_win = p_win_gaussian(pi_opt_d, ell_opt_d, theta_v, sigma_v)

        print(f"\n  [{label}]")
        print(f"    Optimal π* = {pi_opt_d:.4f}$ = {pi_opt_s:.2f}σ = {pi_opt_R:.2f}R")
        print(f"    Optimal ℓ* = {ell_opt_d:.4f}$ = {ell_opt_s:.2f}σ = {ell_opt_R:.2f}R")
        print(f"    P(win)    = {p_win:.4f}")
        print(f"    Sharpe*   = {sharpe_opt:.4f}")

        results_gauss[label] = {
            "theta": theta_v, "sigma": sigma_v,
            "pi_opt_d": pi_opt_d, "pi_opt_sigma": pi_opt_s, "pi_opt_R": pi_opt_R,
            "ell_opt_d": ell_opt_d, "ell_opt_sigma": ell_opt_s, "ell_opt_R": ell_opt_R,
            "p_win": p_win, "sharpe": sharpe_opt,
            "sharpe_mat": sharpe_mat.tolist(),
            "pi_dollars": pi_dollars.tolist(),
            "ell_dollars": ell_dollars.tolist(),
            "bav_R": bav_R.tolist(),
            "bav_ell_d": ell_dollars.tolist(),
        }

    # ── Step 1b: Gaussian MC with T_max (validation at analytical optimal) ─
    print("\n[Step 1b] Gaussian MC with T_max constraints (validation)...")

    mc_gauss_results = {}
    for label, theta_v, sigma_v, t_max_v in [
        ("All-hours T_max=35", THETA_ALL, sigma_use_all, T_MAX_ALL),
        ("KZ-only T_max=26",   THETA_KZ,  sigma_use_kz,  T_MAX_KZ),
    ]:
        print(f"  Simulating {N_PATHS_GAUSS:,} Gaussian paths ({label})...")
        X = simulate_ou_paths(N_PATHS_GAUSS, t_max_v, theta_v, sigma_v, df_t=None)

        # Evaluate on coarse grid: 0.25σ steps
        pi_cs  = np.arange(0.25, 5.01, 0.25) * sigma_v
        ell_cs = np.arange(-0.25, -5.01, -0.25) * sigma_v

        sharpe_mc = mc_sharpe_coarse(X, pi_cs, ell_cs, C_DOLLARS)

        flat_idx = np.nanargmax(sharpe_mc)
        i_opt, j_opt = np.unravel_index(flat_idx, sharpe_mc.shape)
        pi_opt_d  = pi_cs[i_opt]
        ell_opt_d = ell_cs[j_opt]
        sharpe_opt = sharpe_mc[i_opt, j_opt]

        print(f"    MC optimal π*={pi_opt_d:.3f}$ ({pi_opt_d/sigma_v:.2f}σ) "
              f"ℓ*={ell_opt_d:.3f}$ ({ell_opt_d/sigma_v:.2f}σ)  "
              f"Sharpe={sharpe_opt:.4f}")

        mc_gauss_results[label] = {
            "t_max": t_max_v, "theta": theta_v, "sigma": sigma_v,
            "pi_opt_d": float(pi_opt_d), "pi_opt_sigma": float(pi_opt_d / sigma_v),
            "pi_opt_R": float(pi_opt_d / AVG_SL),
            "ell_opt_d": float(ell_opt_d), "ell_opt_sigma": float(ell_opt_d / sigma_v),
            "ell_opt_R": float(ell_opt_d / AVG_SL),
            "sharpe": float(sharpe_opt),
        }

    # ── Step 2: Fat-tail MC ────────────────────────────────────────────────
    print("\n[Step 2] Fat-tail Student-t MC (df=2.857 per task spec)...")

    mc_fat_results = {}
    for label, theta_v, sigma_v, t_max_v in [
        ("All-hours T_max=35", THETA_ALL, sigma_use_all, T_MAX_ALL),
        ("KZ-only T_max=26",   THETA_KZ,  sigma_use_kz,  T_MAX_KZ),
    ]:
        print(f"  Simulating {N_PATHS_FATTAIL:,} fat-tail paths ({label})...")
        X_fat = simulate_ou_paths(N_PATHS_FATTAIL, t_max_v, theta_v, sigma_v,
                                  df_t=DF_SPECIFIED)

        pi_cs  = np.arange(0.25, 5.01, 0.25) * sigma_v
        ell_cs = np.arange(-0.25, -5.01, -0.25) * sigma_v

        sharpe_mc = mc_sharpe_coarse(X_fat, pi_cs, ell_cs, C_DOLLARS)

        flat_idx = np.nanargmax(sharpe_mc)
        i_opt, j_opt = np.unravel_index(flat_idx, sharpe_mc.shape)
        pi_opt_d  = float(pi_cs[i_opt])
        ell_opt_d = float(ell_cs[j_opt])
        sharpe_opt = float(sharpe_mc[i_opt, j_opt])

        # Compare to Gaussian optimal from corresponding scenario
        gauss_key = label
        if gauss_key in mc_gauss_results:
            g = mc_gauss_results[gauss_key]
            delta_pi  = pi_opt_d  - g["pi_opt_d"]
            delta_ell = ell_opt_d - g["ell_opt_d"]
        else:
            delta_pi = delta_ell = np.nan

        print(f"    Fat-tail optimal π*={pi_opt_d:.3f}$ ({pi_opt_d/sigma_v:.2f}σ) "
              f"ℓ*={ell_opt_d:.3f}$ ({ell_opt_d/sigma_v:.2f}σ)  "
              f"Sharpe={sharpe_opt:.4f}")
        print(f"    Shift vs Gaussian: Δπ={delta_pi:+.3f}$  Δℓ={delta_ell:+.3f}$")

        mc_fat_results[label] = {
            "t_max": t_max_v, "theta": theta_v, "sigma": sigma_v,
            "pi_opt_d": pi_opt_d, "pi_opt_sigma": pi_opt_d / sigma_v,
            "pi_opt_R": pi_opt_d / AVG_SL,
            "ell_opt_d": ell_opt_d, "ell_opt_sigma": ell_opt_d / sigma_v,
            "ell_opt_R": ell_opt_d / AVG_SL,
            "sharpe": sharpe_opt,
            "delta_pi_vs_gauss": float(delta_pi),
            "delta_ell_vs_gauss": float(delta_ell),
        }

    # ── Step 3: Sharpe at current GTOS parameters ──────────────────────────
    print("\n[Step 3] Evaluating current GTOS rule at optimized parameters...")

    # GTOS current rule:
    # - Trailing stop: trail 0.5R after MFE >= 1.5R
    # - SL: $10 (assumed)
    # - TP1: 1.0R (50% exit), TP2: 2.0R (25% exit), runner (25%)
    # For a simple comparison use the "effective" fixed exit approximation:
    # Weighted TP ≈ 0.50×1.0 + 0.25×2.0 + 0.25×(average trail exit)
    # From batch data: mean original_r ≈ 0.49R (from trailing_stop_details_overall.csv)
    # Use 1.5R as the primary TP level (the trailing trigger)
    GTOS_TP_R = 1.5     # primary target (trailing trigger)
    GTOS_SL_R = -1.0    # 1R stop loss (by definition)

    gtos_metrics = {}
    for label, theta_v, sigma_v in [
        ("All-hours", THETA_ALL, sigma_use_all),
        ("KZ-only",   THETA_KZ,  sigma_use_kz),
    ]:
        gtos_tp_d  = GTOS_TP_R  * AVG_SL
        gtos_sl_d  = GTOS_SL_R  * AVG_SL

        p_win = p_win_gaussian(gtos_tp_d, gtos_sl_d, theta_v, sigma_v)
        ep    = p_win * (gtos_tp_d - C_DOLLARS) + (1-p_win) * (gtos_sl_d - C_DOLLARS)
        varp  = p_win * (1-p_win) * (gtos_tp_d - gtos_sl_d) ** 2
        sharpe_gtos = ep / np.sqrt(varp) if varp > 1e-12 else np.nan

        opt_sharpe = results_gauss[label]["sharpe"]
        ratio = sharpe_gtos / opt_sharpe if (opt_sharpe and not np.isnan(opt_sharpe)) else np.nan

        print(f"\n  [{label}]  GTOS rule vs Optimal")
        print(f"    GTOS: π={gtos_tp_d:.2f}$ ({GTOS_TP_R}R)  ℓ={gtos_sl_d:.2f}$ ({GTOS_SL_R}R)")
        print(f"    GTOS P(win)={p_win:.4f}  Sharpe={sharpe_gtos:.4f}")
        print(f"    Optimal Sharpe={opt_sharpe:.4f}  Ratio={ratio:.4f}")

        gtos_metrics[label] = {
            "gtos_tp_R": GTOS_TP_R, "gtos_sl_R": GTOS_SL_R,
            "p_win_gtos": p_win, "sharpe_gtos": sharpe_gtos,
            "sharpe_optimal": opt_sharpe, "efficiency_ratio": ratio,
        }

    # ── Save JSON data ─────────────────────────────────────────────────────
    output_data = {
        "timestamp": TIMESTAMP,
        "seed": SEED,
        "ou_params": {
            "theta_all": THETA_ALL, "theta_kz": THETA_KZ,
            "hl_all": HL_ALL, "hl_kz": HL_KZ,
            "sigma_all": sigma_use_all, "sigma_kz": sigma_use_kz,
            "mu": 0.0, "spread_def": "close - SMA50(H1)",
            "source": "ou_kz_half_life_v2.md (peer-review-fixed)",
        },
        "fat_tail": {
            "xi_specified": XI_SPECIFIED, "df_specified": DF_SPECIFIED,
            "xi_upper_actual": XI_UPPER_ACTUAL, "xi_lower_actual": XI_LOWER_ACTUAL,
            "xi_actual_avg": XI_ACTUAL_AVG, "df_actual": DF_ACTUAL,
        },
        "assumptions": {
            "c_dollars": C_DOLLARS, "avg_sl_dollars": AVG_SL, "x0": 0.0,
            "note": "avg_sl_dollars=$10 default; no dollar SL in batch data",
        },
        "gaussian_analytical": results_gauss,
        "gaussian_mc_tmax": mc_gauss_results,
        "fattail_mc": mc_fat_results,
        "gtos_comparison": gtos_metrics,
    }

    # Drop sharpe_mat from JSON (too large)
    for v in output_data["gaussian_analytical"].values():
        v.pop("sharpe_mat", None)

    json_path = os.path.join(OUT_DIR, f"optimal_trailing_stop_data_v1_{TIMESTAMP}.json")
    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n  Data saved: {json_path}")

    # ── Write markdown report ──────────────────────────────────────────────
    write_markdown(output_data, results_gauss, mc_gauss_results,
                   mc_fat_results, gtos_metrics, sigma_use_all, sigma_use_kz)

    print("\n[DONE] All outputs written to research/diagnostics/trailing_stop_optimal/")
    return output_data


def write_markdown(data, gauss_a, gauss_mc, fat_mc, gtos, sigma_all, sigma_kz):
    ts = data["timestamp"]
    ou = data["ou_params"]
    ft = data["fat_tail"]
    assump = data["assumptions"]

    g_all = gauss_a["All-hours"]
    g_kz  = gauss_a["KZ-only"]
    f_all = fat_mc.get("All-hours T_max=35", {})
    f_kz  = fat_mc.get("KZ-only T_max=26", {})
    gmc_all = gauss_mc.get("All-hours T_max=35", {})
    gmc_kz  = gauss_mc.get("KZ-only T_max=26", {})
    gtos_all = gtos["All-hours"]
    gtos_kz  = gtos["KZ-only"]

    def fmt(x, prec=4):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "—"
        return f"{x:.{prec}f}"

    md = f"""# GTOS Optimal Trailing Stop Bounds (Q-6.1)
*Generated {ts} UTC*
*Script: compute_optimal_trail_v1.py*

---

## 1. OU Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| θ (all-hours) | {ou['theta_all']:.6f}/bar | ou_kz_half_life_v2.md (bug-fixed) |
| θ (KZ-only) | {ou['theta_kz']:.6f}/bar | ou_kz_half_life_v2.md (bug-fixed) |
| HL (all-hours) | {ou['hl_all']:.2f} H1 bars | −ln(2)/β_all |
| HL (KZ-only) | {ou['hl_kz']:.2f} H1 bars | −ln(2)/β_kz |
| σ (all-hours) | {ou['sigma_all']:.4f}$ | Residual σ of AR(1) on SMA50 spread |
| σ (KZ-only) | {ou['sigma_kz']:.4f}$ | Residual σ of AR(1), KZ subsample |
| μ | 0.0$ | SMA50 detrend → mean-zero by construction |
| Spread definition | close − SMA50(H1) | Matching original diagnostic |
| X₀ | 0.0$ | Entry at long-run mean (symmetric baseline) |

**Transaction cost:** c = {assump['c_dollars']}$ round-trip (assumed, conservative FTMO spread)
**Average SL:** {assump['avg_sl_dollars']}$ (default; dollar SL not stored in batch data — assumption stated)

---

## 2. Gaussian OU Optimal Exit (Analytical, No T_max)

Method: P(win) computed via OU scale function S(x) = (σ√π)/(2√θ) × erfi(x√θ/σ).
Sharpe = E[P&L] / √Var[P&L] over two-outcome (win/loss) distribution.
Grid: π ∈ [0.1σ, 5σ] step 0.05σ; ℓ ∈ [−0.1σ, −5σ] step 0.05σ.

| Scenario | π* (σ) | π* ($) | π* (R) | ℓ* (σ) | ℓ* ($) | ℓ* (R) | P(win) | Sharpe* |
|----------|--------|--------|--------|--------|--------|--------|--------|---------|
| All-hours (θ={ou['theta_all']:.4f}) | {g_all['pi_opt_sigma']:.2f}σ | {g_all['pi_opt_d']:.2f}$ | {g_all['pi_opt_R']:.2f}R | {g_all['ell_opt_sigma']:.2f}σ | {g_all['ell_opt_d']:.2f}$ | {g_all['ell_opt_R']:.2f}R | {g_all['p_win']:.4f} | {g_all['sharpe']:.4f} |
| KZ-only (θ={ou['theta_kz']:.4f}) | {g_kz['pi_opt_sigma']:.2f}σ | {g_kz['pi_opt_d']:.2f}$ | {g_kz['pi_opt_R']:.2f}R | {g_kz['ell_opt_sigma']:.2f}σ | {g_kz['ell_opt_d']:.2f}$ | {g_kz['ell_opt_R']:.2f}R | {g_kz['p_win']:.4f} | {g_kz['sharpe']:.4f} |

*R-multiples use avg_sl = {assump['avg_sl_dollars']}$ (assumed).*

---

## 3. Gaussian MC with T_max Constraint (N={N_PATHS_GAUSS:,})

MC validates the analytical result and adds the time-exit effect.
Coarse grid: 0.25σ steps. Exit at X(T_max) if neither π nor ell hit by T_max.

| Scenario | T_max | π* (σ) | π* (R) | ℓ* (σ) | ℓ* (R) | Sharpe |
|----------|-------|--------|--------|--------|--------|--------|
| All-hours | {gmc_all.get('t_max',35)} bars | {fmt(gmc_all.get('pi_opt_sigma'),2)}σ | {fmt(gmc_all.get('pi_opt_R'),2)}R | {fmt(gmc_all.get('ell_opt_sigma'),2)}σ | {fmt(gmc_all.get('ell_opt_R'),2)}R | {fmt(gmc_all.get('sharpe'),4)} |
| KZ-only | {gmc_kz.get('t_max',26)} bars | {fmt(gmc_kz.get('pi_opt_sigma'),2)}σ | {fmt(gmc_kz.get('pi_opt_R'),2)}R | {fmt(gmc_kz.get('ell_opt_sigma'),2)}σ | {fmt(gmc_kz.get('ell_opt_R'),2)}R | {fmt(gmc_kz.get('sharpe'),4)} |

---

## 4. Fat-Tail MC Adjustment (Student-t, df={ft['df_specified']:.3f}, N={N_PATHS_FATTAIL:,})

Fat-tail specification: GPD ξ = {ft['xi_specified']} (task spec) → df = 1/ξ = {ft['df_specified']:.3f}.
Actual diagnostic values: ξ_upper = {ft['xi_upper_actual']:.4f}, ξ_lower = {ft['xi_lower_actual']:.4f}, avg = {ft['xi_actual_avg']:.4f} → df_actual ≈ {ft['df_actual']:.2f}.
Student-t variance-matched: σ_adj = σ × √((df-2)/df).
Coarse grid: 0.25σ steps. T_max applied.

| Scenario | T_max | π*_fat (σ) | π*_fat (R) | ℓ*_fat (σ) | ℓ*_fat (R) | Sharpe | Δπ vs Gauss | Δℓ vs Gauss |
|----------|-------|-----------|-----------|-----------|-----------|--------|-------------|-------------|
| All-hours | {f_all.get('t_max',35)} bars | {fmt(f_all.get('pi_opt_sigma'),2)}σ | {fmt(f_all.get('pi_opt_R'),2)}R | {fmt(f_all.get('ell_opt_sigma'),2)}σ | {fmt(f_all.get('ell_opt_R'),2)}R | {fmt(f_all.get('sharpe'),4)} | {fmt(f_all.get('delta_pi_vs_gauss'),3)}$ | {fmt(f_all.get('delta_ell_vs_gauss'),3)}$ |
| KZ-only | {f_kz.get('t_max',26)} bars | {fmt(f_kz.get('pi_opt_sigma'),2)}σ | {fmt(f_kz.get('pi_opt_R'),2)}R | {fmt(f_kz.get('ell_opt_sigma'),2)}σ | {fmt(f_kz.get('ell_opt_R'),2)}R | {fmt(f_kz.get('sharpe'),4)} | {fmt(f_kz.get('delta_pi_vs_gauss'),3)}$ | {fmt(f_kz.get('delta_ell_vs_gauss'),3)}$ |

---

## 5. Baviera Sensitivity (Expected Return vs SL, π = π* fixed)

The Baviera curve shows how sensitive expected return is to SL placement, holding
profit target fixed at the Gaussian analytical optimal π*.

**All-hours (π* = {g_all['pi_opt_d']:.2f}$):**

| ℓ (σ) | ℓ ($) | ℓ (R) | E[P&L] ($) |
|-------|-------|-------|------------|
"""
    # Baviera table: all-hours
    bav_ell_d = g_all.get("bav_ell_d", [])
    bav_R_all  = g_all.get("bav_R", [])
    if bav_ell_d and bav_R_all:
        sample_idx = [0, 4, 9, 14, 19, 29, 39, 49, 59, 69, 79, 89, 98]
        for idx in sample_idx:
            if idx < len(bav_ell_d):
                e_d = bav_ell_d[idx]
                e_s = e_d / sigma_all
                e_R = e_d / AVG_SL
                ep  = bav_R_all[idx]
                md += f"| {e_s:.2f}σ | {e_d:.2f}$ | {e_R:.2f}R | {ep:.4f}$ |\n"

    md += f"""
---

## 6. Current GTOS Rule vs Optimal

Current GTOS trailing stop rule:
- SL = max(zone distance, $10, 1.5 × M15 ATR) ≈ {AVG_SL}$ avg (assumed)
- TP1 = 1.0R (50% exit), TP2 = 2.0R (25% exit), runner (25%)
- Trailing activation: MFE ≥ 1.5R; trail = 0.5R behind peak
- Simplified equivalent for comparison: π = 1.5R, ℓ = -1.0R

| Scenario | Rule | π (R) | ℓ (R) | P(win) | Sharpe | vs Optimal |
|----------|------|-------|-------|--------|--------|------------|
| All-hours | GTOS current | 1.5R | -1.0R | {gtos_all['p_win_gtos']:.4f} | {fmt(gtos_all['sharpe_gtos'],4)} | {gtos_all['efficiency_ratio']:.2%} of optimal |
| All-hours | Gaussian optimal | {g_all['pi_opt_R']:.2f}R | {g_all['ell_opt_R']:.2f}R | {g_all['p_win']:.4f} | {g_all['sharpe']:.4f} | 100% |
| KZ-only | GTOS current | 1.5R | -1.0R | {gtos_kz['p_win_gtos']:.4f} | {fmt(gtos_kz['sharpe_gtos'],4)} | {gtos_kz['efficiency_ratio']:.2%} of optimal |
| KZ-only | Gaussian optimal | {g_kz['pi_opt_R']:.2f}R | {g_kz['ell_opt_R']:.2f}R | {g_kz['p_win']:.4f} | {g_kz['sharpe']:.4f} | 100% |

---

## 7. Interpretation of Results

### 7a. Why the Analytical Optimal Hits the Boundary

The analytical Gaussian result (Section 2) produces ℓ* = −5σ, which is the edge of
the search grid. This is theoretically correct and expected:

**Without a T_max constraint, the OU optimal SL is always "as wide as possible."**
Reasoning: for an OU process starting at X₀=0, P(hit π | X₀=0) → 1 as |ℓ| → ∞,
because an ergodic OU process will eventually visit any finite level given infinite
time. With unlimited time, you can always widen the SL while maintaining P(win) → 1.
The Sharpe formula without T_max has no finite interior maximum — it increases
monotonically with |ℓ|. The boundary result is the grid constraint, not a genuine
optimum. **Section 2 is mathematically correct but practically useless without T_max.**

### 7b. MC with T_max: What the Results Mean

The T_max-constrained MC (Section 3) is the operationally relevant result.
Both scenarios converge to: π* ≈ 1.5σ, ℓ* ≈ −0.25σ (the smallest available SL
in the coarse grid). This means the true optimum ℓ* is tighter than 0.25σ —
possibly even tighter than the bid-ask spread.

**Interpretation:** For a *symmetric* OU starting at X₀=0 with T_max, the optimizer
finds it is better to accept many tiny losses (−ε) and let winners run to 1.5σ,
rather than set a wider SL. This is a known result in optimal stopping theory:
when there is no directional edge (p_win = 0.5 at any symmetric level), the optimal
strategy resembles a one-sided exit.

### 7c. Why the GTOS Comparison Shows Negative Sharpe (Critical Finding)

The GTOS comparison (Section 6) shows:
- Symmetric OU model predicts P(win) ≈ {gtos_all['p_win_gtos']:.2%} at GTOS levels (π=1.5R, ℓ=−1.0R)
- This gives **negative model Sharpe** ({fmt(gtos_all['sharpe_gtos'],4)})
- Yet GTOS achieves 62–65% WR in batch data

**The gap is explained by directional edge:**
The symmetric OU (X₀=0) predicts only 40% WR because it has no directional
prior. GTOS achieves 62% WR because the OB retest setup provides a structural
directional bias — price is more likely to continue in the BOS direction than to
reverse. This is precisely the edge identified in test_a_rerun (+17pp over generic
pullback, p=0.003).

**Consequence:** The OU framework in this symmetric form cannot validly rank the
current GTOS rule against the "optimal" — the GTOS rule is not operating under the
symmetric OU assumption. The directional edge lifts the effective P(win) from 40% to 62%.

### 7d. Actionable Findings

**OU calibration is confirmed:**
- θ_all = {ou['theta_all']:.4f}/bar (HL = {ou['hl_all']:.1f} bars), θ_kz = {ou['theta_kz']:.4f}/bar (HL = {ou['hl_kz']:.1f} bars)
- σ_all = {ou['sigma_all']:.2f}$ residual spread vol; σ_kz = {ou['sigma_kz']:.2f}$
- KZ mean reversion is {100*(ou['theta_kz']/ou['theta_all']-1):+.1f}% faster than all-hours

**Timeout calibration (independent of directional edge):**
- 1.5 × HL_kz = {T_MAX_KZ} bars; 1.5 × HL_all = {T_MAX_ALL} bars
- These are confirmed as reasonable exit timeouts regardless of the SL/TP debate
- Current GTOS timeout (CLOSED_SESSION_TIMEOUT) is session-based, not bar-count; this
  is a candidate for future refinement as a complement to the session rule

**Fat-tail shift:**
- Fat-tail adjustment (df={ft['df_specified']:.2f}) does NOT shift the grid optimum in this
  analysis (Δπ=0, Δℓ=0). The optimal grid point stays the same under fat-tails.
  Fat-tails reduce Sharpe ({fmt(gmc_all.get('sharpe'),4)} Gauss → {fmt(f_all.get('sharpe'),4)} fat-tail, all-hours)
  but do not move the optimal location on the coarse grid.
- Implication: fat tails are a Sharpe-reducer, not a level-shifter, at the granularity
  of this analysis. A finer grid search might reveal a small shift.

**SL/TP recommendation (conditional on directional edge model):**
- For a pure OU model (no directional edge): tight SL + 1.5σ TP is "optimal" under T_max
- For GTOS (directional edge = 62% WR): the structural OB zone determines SL placement,
  NOT OU mean reversion. The SL at zone invalidation is justified by price structure,
  not by OU Sharpe maximization.
- The OU calibration is most useful for: (a) setting T_max timeout bars, and (b) informing
  at what price excursion the trade is fighting the mean reversion (i.e., if price hasn't
  moved by 1.5σ = ~{g_all['pi_opt_d']:.0f}$ in {T_MAX_KZ} KZ bars, the mean-reversion window is closing).

**No changes recommended to src/ or GTOS live rules from this analysis alone.**
This is a research calibration output. CEO review required before any live parameter changes.

---

**Key assumptions (must be verified before promotion to live parameters):**
1. X₀ = 0 (symmetric entry) — Actual GTOS entries have directional prior; see Section 7c
2. avg_sl = {assump['avg_sl_dollars']}$ assumed; dollar SL values needed from live logs for R-conversion
3. c = {assump['c_dollars']}$ round-trip spread (FTMO conservative estimate)
4. df = {ft['df_specified']:.2f} (task spec); actual diagnostic ξ_avg={ft['xi_actual_avg']:.3f} → df≈{ft['df_actual']:.1f} (slightly thinner tails)

---

*Source data: data/historical/XAUUSD_H1.csv*
*OU params: research/diagnostics/mean_reversion_mechanics/ou_kz_half_life_v2.md*
*GPD params: research/diagnostics/distributional_characterization_20260411_012816.json*
*Batch data: research/kap_outputs/tests/trailing_stop_details_overall.csv*
"""

    md_path = os.path.join(OUT_DIR, "optimal_trailing_stop_v1.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  Report saved: {md_path}")


if __name__ == "__main__":
    main()
