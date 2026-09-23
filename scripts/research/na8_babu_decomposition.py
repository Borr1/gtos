"""NA8 — Babu-Hoffman-Levine 2020 decomposition of XAUUSD H1->H2 2026 LONG decay.

GATES Q1.4 priority order between H-1 (K54 v3 architecture) and H-2 (Component 3C
Vol-Conditioning). If move-magnitude attribution >=40% of total decay,
vol-managed sizing alone is predicted to recover >=20% of realized-R loss in
production (post-50% literature haircut), and H-2 ships ahead of H-1.

PRE-REGISTERED HYPOTHESIS (locked before any data was inspected):
  "Babu-Hoffman-Levine 2020 decomposition of H1->H2 XAUUSD LONG cohort decay
  attributes >=40% of the realized-R degradation to move-magnitude (vol regime
  difference between H1 and H2), with stationary-bootstrap-corrected SE. If
  true, vol-managed sizing alone (Barroso-Santa-Clara 2015 sigma multiplier on
  realized-vol percentile, clipped to [0.5, 2.0]) is predicted to recover
  >=40% x 50% realization-haircut = >=20% of the realized-R loss in production.
  Threshold for Q1.4 priority verdict: >=40% move-magnitude attribution -> H-2
  ships ahead of H-1; <40% -> H-1 K54 v3 architecture is the Q1.4 ship."

Methodology (Babu-Hoffman-Levine 2020, "You Can't Always Trend When You Want"):
  Total decay = mean(R_H2) - mean(R_H1)
  = (mean(vol_H2 * signal_H2) + cross + diversification)
  - (mean(vol_H1 * signal_H1) + cross + diversification)

  Decomposition (additive identity):
    Move-magnitude   = mean(vol_H2) * mean(signal_H1) - mean(vol_H1) * mean(signal_H1)
                     = (mean(vol_H2) - mean(vol_H1)) * mean(signal_H1)
    Signal-trans.    = mean(vol_H1) * mean(signal_H2) - mean(vol_H1) * mean(signal_H1)
                     = mean(vol_H1) * (mean(signal_H2) - mean(signal_H1))
    Diversification  = (mean(vol_H2) - mean(vol_H1)) * (mean(signal_H2) - mean(signal_H1))
                       = interaction term

  In CTA-style decomposition, "vol" = realized vol percentile (size multiplier
  in Barroso-style scheme); "signal" = sign-correctness x conditional R given
  fired. We operationalize as:

    realized_R per trade = position_size_multiplier * raw_R_per_unit_risk
                         ~ (vol_percentile_inverse) * (sign_correctness * unit_R)

  Counterfactual re-sizing: re-scale H2 trades using H1's vol-percentile
  distribution (Barroso-Santa-Clara sigma multiplier, clipped [0.5, 2.0]) and
  recompute mean R. The difference vs actual H2 = move-magnitude attribution.

Stationary block bootstrap (Politis-Romano 1994):
  B = 1000 resamples; geometric block length with mean = max(5, AR1_lag).
  Per-component SE + 95% CI computed from bootstrap distribution.

USAGE:
    python scripts/research/na8_babu_decomposition.py \\
        --cands research/decay_diagnostic/A5_regime_matrix/cands_with_regime.jsonl \\
        --h4 data/historical_2026/XAUUSD_H4.csv \\
        --out research/ml_program/experiments/na8_babu_results.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Period & FA-2 boundaries
# CANONICAL period split per scripts/research/run_a6_decay_attribution.py:
#   H1 = 2026-01 + 2026-02 (Jan + Feb)
#   H2 = 2026-03 + 2026-04 (Mar + Apr)
# This OVERRIDES the brief's H1=Jan-Apr13/H2=Apr14-Apr28 split, because A6
# (the upstream attribution that this NA8 task decomposes) uses the
# month-bucket split. Using the canonical split here keeps NA8 directly
# comparable to A6 numbers (H1 n=63, H2 n=44, observed +8.98pp WR delta).
# ---------------------------------------------------------------------------

H1_MONTHS = {"2026-01", "2026-02"}
H2_MONTHS = {"2026-03", "2026-04"}

# FA-2 commit fa35cc0 timestamp: 2026-04-20 03:57 +0800 = 2026-04-19T19:57:00Z
# This boundary slices H2 itself (since H2 = Mar+Apr).
FA2_BOUNDARY = pd.Timestamp("2026-04-19T19:57:00Z")

# Vol-managed sizing clip (Barroso-Santa-Clara 2015): sigma multiplier in [0.5, 2.0]
SIGMA_MULT_CLIP = (0.5, 2.0)

# Bootstrap config
BOOTSTRAP_B = 1000
BOOTSTRAP_SEED = 17  # pre-registered, never tuned
BOOTSTRAP_BLOCK_LEN_MIN = 5

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_xauusd_long_cohort(path: str | Path) -> pd.DataFrame:
    """Load XAUUSD LONG-side trade ledger from cands_with_regime.jsonl."""
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("symbol") != "XAUUSD":
                continue
            if d.get("direction") != "LONG":
                continue
            if d.get("decision") != "CANDIDATE":
                continue
            r = d.get("r_multiple")
            if r is None:
                continue
            ts = pd.Timestamp(d.get("candle_close_time")).tz_convert("UTC")
            rows.append(
                {
                    "ts": ts,
                    "kill_zone": d.get("kill_zone"),
                    "regime": d.get("regime"),
                    "outcome": d.get("outcome"),
                    "r_multiple": float(r),
                    "entry_price": d.get("entry_price"),
                    "stop_loss": d.get("stop_loss"),
                }
            )
    df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)

    # Bucket into period using A6's canonical month-bucket split
    df["period_month"] = df["ts"].dt.strftime("%Y-%m")
    df["period"] = "OOS"
    df.loc[df["period_month"].isin(H1_MONTHS), "period"] = "H1"
    df.loc[df["period_month"].isin(H2_MONTHS), "period"] = "H2"

    # FA-2 split for H2 (FA-2 falls inside Apr, which is part of H2)
    df["fa2_segment"] = "n/a"
    h2_mask = df["period"] == "H2"
    df.loc[h2_mask & (df["ts"] < FA2_BOUNDARY), "fa2_segment"] = "pre_fa2"
    df.loc[h2_mask & (df["ts"] >= FA2_BOUNDARY), "fa2_segment"] = "post_fa2"

    return df


def load_h4_ohlcv(path: str | Path) -> pd.DataFrame:
    """Load H4 OHLCV; compute realized vol (sigma_20H4) & ATR-percentile.

    realized_vol = rolling 20-bar (5d) std of log returns, annualized.
    """
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)

    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
    # 20-H4-bar (~5 trading day) window, annualize: sqrt(N_bars_per_year)
    # 6 H4 bars/day x 252 days = 1512 bars/year
    df["realized_vol_20H4"] = df["log_ret"].rolling(20).std() * np.sqrt(1512)

    # Percentile rank within full sample for size-multiplier inversion
    df["realized_vol_rank"] = df["realized_vol_20H4"].rank(pct=True)

    # Barroso-Santa-Clara 2015 vol-managed sigma multiplier
    # sigma_target / sigma_realized; we use median-vol target so multiplier ~1
    median_vol = df["realized_vol_20H4"].median()
    df["bsc_sigma_mult"] = median_vol / df["realized_vol_20H4"]
    df["bsc_sigma_mult"] = df["bsc_sigma_mult"].clip(*SIGMA_MULT_CLIP)

    return df


def attach_vol_to_trades(trades: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    """For each trade, find the most recent H4 bar at-or-before trade ts; copy vol."""
    h4_indexed = h4.set_index("time").sort_index()
    out = trades.copy()
    vols = []
    ranks = []
    sigma_mults = []
    for ts in out["ts"]:
        # asof lookup: most recent H4 bar at-or-before trade ts
        idx = h4_indexed.index.searchsorted(ts, side="right") - 1
        if idx < 0 or idx >= len(h4_indexed):
            vols.append(np.nan)
            ranks.append(np.nan)
            sigma_mults.append(np.nan)
            continue
        row = h4_indexed.iloc[idx]
        vols.append(float(row["realized_vol_20H4"]))
        ranks.append(float(row["realized_vol_rank"]))
        sigma_mults.append(float(row["bsc_sigma_mult"]))
    out["realized_vol"] = vols
    out["realized_vol_rank"] = ranks
    out["bsc_sigma_mult"] = sigma_mults
    return out


# ---------------------------------------------------------------------------
# Babu-Hoffman-Levine decomposition
# ---------------------------------------------------------------------------


def babu_decompose(
    h1_trades: pd.DataFrame, h2_trades: pd.DataFrame
) -> dict[str, float]:
    """Decompose total decay (mean R) into Babu-style components.

    The Babu et al. 2020 framework (CTA paper) decomposes
    mean_R(period) = mean(size_multiplier * signal_R)

    where size_multiplier ~= bsc_sigma_mult (Barroso vol-managed)
    and signal_R = raw R-multiple (signal-translation: AI's directional call quality).

    Decomposition (additive identity for mean(X*Y)):
      mean(X_2 * Y_2) - mean(X_1 * Y_1)
      = (mean(X_2) - mean(X_1)) * mean(Y_1)    # MOVE-MAGNITUDE
      + mean(X_1) * (mean(Y_2) - mean(Y_1))    # SIGNAL-TRANSLATION
      + (cov(X_2,Y_2) - cov(X_1,Y_1))          # DIVERSIFICATION (interaction)
      + (mean(X_2) - mean(X_1)) * (mean(Y_2) - mean(Y_1))  # cross term (small)

    In Babu et al., "diversification" captures the interaction-vs-marginal
    differential. For our two-component case the cleanest closure is:
      Total = MoveMag + SignalTrans + Diversification (residual)

    where Diversification = Total - MoveMag - SignalTrans.
    """
    x1 = h1_trades["bsc_sigma_mult"].values
    y1 = h1_trades["r_multiple"].values
    x2 = h2_trades["bsc_sigma_mult"].values
    y2 = h2_trades["r_multiple"].values

    # mean realized R = mean(size * signal_R) -- under our operationalization
    # where size_mult = 1 in the AS-TRADED period (no vol-managed sizing live).
    # The AS-TRADED mean is just mean(y).
    # We re-construct Babu by treating mean(y) as the FULL realized R, and
    # computing what would happen if size_mult had varied = bsc_sigma_mult.

    # AS-TRADED (current production: size_mult = 1 always)
    h1_actual = float(np.mean(y1))
    h2_actual = float(np.mean(y2))
    total_decay = h2_actual - h1_actual  # negative if H2 worse (decay)

    # Counterfactual H2 with H1-vol-regime size: H2 trades get H1's avg vol-mult
    # MoveMagnitude attribution = (E[X2]-E[X1]) * E[Y1]
    #   (signed so that positive => move-magnitude EXPLAINS decay if both terms negative)
    e_x1 = float(np.mean(x1))
    e_x2 = float(np.mean(x2))
    e_y1 = float(np.mean(y1))
    e_y2 = float(np.mean(y2))

    move_mag = (e_x2 - e_x1) * e_y1
    signal_trans = e_x1 * (e_y2 - e_y1)
    cross_term = (e_x2 - e_x1) * (e_y2 - e_y1)
    cov_diff = (
        float(np.cov(x2, y2, ddof=0)[0, 1]) - float(np.cov(x1, y1, ddof=0)[0, 1])
    )
    diversification_residual = total_decay - (move_mag + signal_trans + cross_term)

    # Sum check (Babu identity): MoveMag + SignalTrans + Cross + DivResid = Total
    sum_check = move_mag + signal_trans + cross_term + diversification_residual
    closure_error = total_decay - sum_check

    return {
        "h1_n": int(len(h1_trades)),
        "h2_n": int(len(h2_trades)),
        "h1_actual_mean_R": h1_actual,
        "h2_actual_mean_R": h2_actual,
        "total_decay_R": total_decay,
        "h1_mean_size_mult": e_x1,
        "h2_mean_size_mult": e_x2,
        "move_magnitude_R": move_mag,
        "signal_translation_R": signal_trans,
        "cross_term_R": cross_term,
        "covariance_diff_R": cov_diff,
        "diversification_R": diversification_residual,
        "sum_check_R": sum_check,
        "closure_error_R": closure_error,
    }


def vol_managed_recovery(
    h1_trades: pd.DataFrame,
    h2_trades: pd.DataFrame,
    haircut: float = 0.5,
) -> dict[str, float]:
    """Estimate Barroso-Santa-Clara recovery: re-size H2 trades by their bsc_sigma_mult.

    Production (current): size_mult = 1 always; mean R = mean(y).
    Counterfactual:       size_mult = bsc_sigma_mult; mean R = mean(bsc_sigma_mult * y).

    Recovery percent of decay = (counterfactual H2 R - actual H2 R) / |total_decay|

    Apply 50% literature realization haircut for production estimate.
    """
    y1 = h1_trades["r_multiple"].values
    y2 = h2_trades["r_multiple"].values
    x2 = h2_trades["bsc_sigma_mult"].values

    h1_actual = float(np.mean(y1))
    h2_actual = float(np.mean(y2))
    total_decay = h2_actual - h1_actual

    h2_vol_managed = float(np.mean(x2 * y2))
    counterfactual_recovery_R = h2_vol_managed - h2_actual
    if abs(total_decay) > 1e-12:
        recovery_pct_of_decay = counterfactual_recovery_R / abs(total_decay)
    else:
        recovery_pct_of_decay = 0.0

    haircut_recovery_R = counterfactual_recovery_R * (1.0 - haircut)
    haircut_pct_of_decay = recovery_pct_of_decay * (1.0 - haircut)

    return {
        "h2_actual_mean_R": h2_actual,
        "h2_vol_managed_mean_R": h2_vol_managed,
        "literature_recovery_R": counterfactual_recovery_R,
        "literature_recovery_pct_of_decay": recovery_pct_of_decay,
        "post_haircut_recovery_R": haircut_recovery_R,
        "post_haircut_pct_of_decay": haircut_pct_of_decay,
        "haircut_used": haircut,
    }


# ---------------------------------------------------------------------------
# Stationary block bootstrap (Politis-Romano 1994)
# ---------------------------------------------------------------------------


def estimate_ar1_lag(series: np.ndarray) -> int:
    """Estimate AR(1) lag for setting bootstrap block length."""
    n = len(series)
    if n < 5:
        return BOOTSTRAP_BLOCK_LEN_MIN
    # AR(1) coefficient
    s = series - np.mean(series)
    rho = float(np.dot(s[:-1], s[1:]) / max(np.dot(s[:-1], s[:-1]), 1e-12))
    rho = max(-0.99, min(0.99, rho))
    # Politis-White block length heuristic: b ~ n^(1/3); we use a simpler
    # "decorrelation horizon" = ceil(1 / (1 - |rho|)) clipped to >= MIN
    if abs(rho) < 1e-3:
        return BOOTSTRAP_BLOCK_LEN_MIN
    horizon = int(math.ceil(1.0 / max(1e-3, 1.0 - abs(rho))))
    return max(BOOTSTRAP_BLOCK_LEN_MIN, min(horizon, n // 4))


def stationary_block_resample(
    arr: np.ndarray, block_len: int, rng: np.random.Generator
) -> np.ndarray:
    """One stationary block-bootstrap sample of length len(arr).

    Block lengths are geometric(1/block_len). Starting indices are uniform.
    """
    n = len(arr)
    if n == 0:
        return arr.copy()
    out = np.empty(n, dtype=arr.dtype)
    i = 0
    while i < n:
        start = rng.integers(0, n)
        L = rng.geometric(1.0 / block_len)
        L = min(L, n - i)
        for k in range(L):
            out[i + k] = arr[(start + k) % n]
        i += L
    return out


def bootstrap_decomposition(
    h1_trades: pd.DataFrame,
    h2_trades: pd.DataFrame,
    B: int = BOOTSTRAP_B,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, dict[str, float]]:
    """Run B stationary-bootstrap resamples; return per-component CI."""
    rng = np.random.default_rng(seed)
    # Block length: estimate AR1 lag on combined R series
    combined_R = np.concatenate(
        [h1_trades["r_multiple"].values, h2_trades["r_multiple"].values]
    )
    block_len = estimate_ar1_lag(combined_R)

    h1_x = h1_trades["bsc_sigma_mult"].values.copy()
    h1_y = h1_trades["r_multiple"].values.copy()
    h2_x = h2_trades["bsc_sigma_mult"].values.copy()
    h2_y = h2_trades["r_multiple"].values.copy()

    keys = [
        "total_decay_R",
        "move_magnitude_R",
        "signal_translation_R",
        "cross_term_R",
        "diversification_R",
        "h2_vol_managed_mean_R",
        "literature_recovery_R",
        "literature_recovery_pct_of_decay",
        "move_mag_pct_of_decay",
    ]
    samples: dict[str, list[float]] = {k: [] for k in keys}

    for _ in range(B):
        # Resample within-period (preserves period split)
        # Resample indices, then re-align x,y (joint resample preserves cov)
        idx1 = rng.integers(0, len(h1_y), size=len(h1_y))
        # Stationary block bootstrap on indices
        idx1 = stationary_block_resample(np.arange(len(h1_y)), block_len, rng)
        idx2 = stationary_block_resample(np.arange(len(h2_y)), block_len, rng)

        x1b = h1_x[idx1]
        y1b = h1_y[idx1]
        x2b = h2_x[idx2]
        y2b = h2_y[idx2]

        e_x1 = float(np.mean(x1b))
        e_x2 = float(np.mean(x2b))
        e_y1 = float(np.mean(y1b))
        e_y2 = float(np.mean(y2b))

        h1_actual = e_y1
        h2_actual = e_y2
        total_decay = h2_actual - h1_actual

        move_mag = (e_x2 - e_x1) * e_y1
        signal_trans = e_x1 * (e_y2 - e_y1)
        cross_term = (e_x2 - e_x1) * (e_y2 - e_y1)
        diversification_resid = total_decay - (move_mag + signal_trans + cross_term)

        h2_vol_managed = float(np.mean(x2b * y2b))
        recovery_R = h2_vol_managed - h2_actual

        if abs(total_decay) > 1e-12:
            recovery_pct = recovery_R / abs(total_decay)
            move_mag_pct = move_mag / abs(total_decay)
        else:
            recovery_pct = 0.0
            move_mag_pct = 0.0

        samples["total_decay_R"].append(total_decay)
        samples["move_magnitude_R"].append(move_mag)
        samples["signal_translation_R"].append(signal_trans)
        samples["cross_term_R"].append(cross_term)
        samples["diversification_R"].append(diversification_resid)
        samples["h2_vol_managed_mean_R"].append(h2_vol_managed)
        samples["literature_recovery_R"].append(recovery_R)
        samples["literature_recovery_pct_of_decay"].append(recovery_pct)
        samples["move_mag_pct_of_decay"].append(move_mag_pct)

    summaries: dict[str, dict[str, float]] = {}
    for k, vals in samples.items():
        a = np.asarray(vals)
        summaries[k] = {
            "mean": float(np.mean(a)),
            "se": float(np.std(a, ddof=1)),
            "ci_low": float(np.quantile(a, 0.025)),
            "ci_high": float(np.quantile(a, 0.975)),
            "ci_25": float(np.quantile(a, 0.25)),
            "ci_75": float(np.quantile(a, 0.75)),
        }
    summaries["_meta"] = {
        "B": B,
        "seed": seed,
        "block_length": block_len,
        "ar1_estimate_basis": "combined_R",
    }
    return summaries


# ---------------------------------------------------------------------------
# Q1.4 priority verdict
# ---------------------------------------------------------------------------


def q1_4_verdict(
    move_mag_pct_of_decay: float,
    bootstrap_summary: dict[str, dict[str, float]],
    threshold: float = 0.40,
) -> dict[str, Any]:
    """Apply pre-registered threshold: >=40% move-mag => H-2 first; else H-1 first."""
    pct = move_mag_pct_of_decay
    bootstrap_pct = bootstrap_summary.get("move_mag_pct_of_decay", {})
    pct_ci_low = bootstrap_pct.get("ci_low", float("nan"))
    pct_ci_high = bootstrap_pct.get("ci_high", float("nan"))

    if pct >= threshold:
        verdict = "H-2 SHIPS AHEAD OF H-1 (vol-conditioning prioritized)"
        rationale = (
            f"Move-magnitude attribution = {pct:.1%} >= {threshold:.0%} threshold; "
            f"vol-managed sizing predicted to recover >=20% of decay (post-haircut)."
        )
    else:
        verdict = "H-1 K54 v3 ARCHITECTURE IS THE Q1.4 SHIP (prompt overhaul prioritized)"
        rationale = (
            f"Move-magnitude attribution = {pct:.1%} < {threshold:.0%} threshold; "
            f"signal-translation/diversification dominate; prompt-overhaul (K54 v3) is the higher-yield investment."
        )

    return {
        "threshold": threshold,
        "move_mag_pct_of_decay": pct,
        "move_mag_pct_ci_95": [pct_ci_low, pct_ci_high],
        "verdict": verdict,
        "rationale": rationale,
        "ci_overlaps_threshold": (pct_ci_low <= threshold <= pct_ci_high)
        if not (math.isnan(pct_ci_low) or math.isnan(pct_ci_high))
        else None,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def cohort_summary(df: pd.DataFrame) -> dict[str, Any]:
    if len(df) == 0:
        return {
            "n": 0,
            "mean_R": None,
            "wr": None,
            "vol_p25": None,
            "vol_p50": None,
            "vol_p75": None,
            "kill_zone_breakdown": {},
            "regime_breakdown": {},
        }
    return {
        "n": int(len(df)),
        "mean_R": float(df["r_multiple"].mean()),
        "median_R": float(df["r_multiple"].median()),
        "wr": float((df["r_multiple"] > 0).mean()),
        "vol_p25": float(df["realized_vol"].quantile(0.25)),
        "vol_p50": float(df["realized_vol"].quantile(0.50)),
        "vol_p75": float(df["realized_vol"].quantile(0.75)),
        "vol_mean": float(df["realized_vol"].mean()),
        "vol_rank_mean": float(df["realized_vol_rank"].mean()),
        "bsc_sigma_mult_mean": float(df["bsc_sigma_mult"].mean()),
        "kill_zone_breakdown": df["kill_zone"].value_counts().to_dict(),
        "regime_breakdown": df["regime"].value_counts().to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cands",
        default="research/decay_diagnostic/A5_regime_matrix/cands_with_regime.jsonl",
    )
    parser.add_argument("--h4", default="data/historical_2026/XAUUSD_H4.csv")
    parser.add_argument(
        "--out", default="research/ml_program/experiments/na8_babu_results.json"
    )
    parser.add_argument("--bootstrap-B", type=int, default=BOOTSTRAP_B)
    parser.add_argument("--threshold", type=float, default=0.40)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    cands_path = (repo_root / args.cands).resolve()
    h4_path = (repo_root / args.h4).resolve()
    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[NA8] Loading XAUUSD LONG cohort from {cands_path}")
    trades = load_xauusd_long_cohort(cands_path)
    print(f"[NA8] Total XAUUSD LONG CANDIDATEs: {len(trades)}")

    print(f"[NA8] Loading H4 OHLCV from {h4_path}")
    h4 = load_h4_ohlcv(h4_path)
    print(
        f"[NA8] H4 bars: {len(h4)}; range {h4['time'].iloc[0]} -> {h4['time'].iloc[-1]}"
    )

    print("[NA8] Joining vol regime to trades")
    trades = attach_vol_to_trades(trades, h4)

    # Drop trades with missing vol (out-of-OHLCV-range)
    pre_n = len(trades)
    trades = trades.dropna(subset=["realized_vol", "bsc_sigma_mult"]).reset_index(
        drop=True
    )
    if len(trades) < pre_n:
        print(f"[NA8]  dropped {pre_n - len(trades)} trades with no H4 coverage")

    h1 = trades[trades["period"] == "H1"].reset_index(drop=True)
    h2 = trades[trades["period"] == "H2"].reset_index(drop=True)
    h2_pre_fa2 = h2[h2["fa2_segment"] == "pre_fa2"].reset_index(drop=True)
    h2_post_fa2 = h2[h2["fa2_segment"] == "post_fa2"].reset_index(drop=True)

    print(
        f"[NA8] H1 LONG n={len(h1)}; H2 LONG n={len(h2)} "
        f"(pre-FA-2 n={len(h2_pre_fa2)}, post-FA-2 n={len(h2_post_fa2)})"
    )

    h1_summary = cohort_summary(h1)
    h2_summary = cohort_summary(h2)
    h2_pre_summary = cohort_summary(h2_pre_fa2)
    h2_post_summary = cohort_summary(h2_post_fa2)

    print("[NA8] Babu decomposition (pooled H2)")
    pooled = babu_decompose(h1, h2)
    pooled_recovery = vol_managed_recovery(h1, h2)

    print("[NA8] Babu decomposition (pre-FA-2 H2 only)")
    if len(h2_pre_fa2) >= 5:
        pre_decomp = babu_decompose(h1, h2_pre_fa2)
        pre_recovery = vol_managed_recovery(h1, h2_pre_fa2)
    else:
        pre_decomp = {"_note": f"insufficient H2 pre-FA-2 n ({len(h2_pre_fa2)})"}
        pre_recovery = pre_decomp

    print("[NA8] Babu decomposition (post-FA-2 H2 only)")
    if len(h2_post_fa2) >= 5:
        post_decomp = babu_decompose(h1, h2_post_fa2)
        post_recovery = vol_managed_recovery(h1, h2_post_fa2)
    else:
        post_decomp = {"_note": f"insufficient H2 post-FA-2 n ({len(h2_post_fa2)})"}
        post_recovery = post_decomp

    print(f"[NA8] Stationary block bootstrap (B={args.bootstrap_B}, seed={BOOTSTRAP_SEED})")
    bootstrap = bootstrap_decomposition(h1, h2, B=args.bootstrap_B)

    # Q1.4 verdict (uses pooled H2)
    if abs(pooled["total_decay_R"]) > 1e-12:
        move_mag_pct = pooled["move_magnitude_R"] / abs(pooled["total_decay_R"])
    else:
        move_mag_pct = 0.0
    verdict = q1_4_verdict(move_mag_pct, bootstrap, threshold=args.threshold)

    # Sensitivity: also compute verdict on pre-FA-2 only (the "non-fixed" regime)
    if isinstance(pre_decomp, dict) and "total_decay_R" in pre_decomp and abs(pre_decomp["total_decay_R"]) > 1e-12:
        pre_move_mag_pct = pre_decomp["move_magnitude_R"] / abs(pre_decomp["total_decay_R"])
    else:
        pre_move_mag_pct = float("nan")

    if isinstance(post_decomp, dict) and "total_decay_R" in post_decomp and abs(post_decomp["total_decay_R"]) > 1e-12:
        post_move_mag_pct = post_decomp["move_magnitude_R"] / abs(post_decomp["total_decay_R"])
    else:
        post_move_mag_pct = float("nan")

    output = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task": "NA8 — Babu-Hoffman-Levine 2020 decomposition",
        "pre_registered_hypothesis": (
            "Babu-Hoffman-Levine 2020 decomposition of H1->H2 XAUUSD LONG cohort "
            "decay attributes >=40% of the realized-R degradation to "
            "move-magnitude (vol regime difference between H1 and H2), with "
            "stationary-bootstrap-corrected SE. If true, vol-managed sizing "
            "alone (Barroso-Santa-Clara 2015 sigma multiplier on realized-vol "
            "percentile, clipped to [0.5, 2.0]) is predicted to recover "
            ">=40% x 50% realization-haircut = >=20% of the realized-R loss in "
            "production. Threshold for Q1.4 priority verdict: >=40% "
            "move-magnitude attribution -> H-2 ships ahead of H-1; <40% -> "
            "H-1 K54 v3 architecture is the Q1.4 ship."
        ),
        "data_sources": {
            "trades": str(cands_path.relative_to(repo_root)),
            "h4_ohlcv": str(h4_path.relative_to(repo_root)),
        },
        "period_definitions": {
            "h1_months": sorted(H1_MONTHS),
            "h2_months": sorted(H2_MONTHS),
            "fa2_boundary_utc": str(FA2_BOUNDARY),
            "fa2_commit": "fa35cc03d57f9a327b15af730f7ec42a06729ee3",
            "fa2_commit_msg": "feat(fa-2): FX precision + sl_buffer_applied + XAUUSD 0.5%",
            "split_choice_rationale": (
                "Use A6's canonical month-bucket split (H1=Jan+Feb, H2=Mar+Apr) so "
                "NA8 numbers are directly comparable to A6 n=63/44 cohort. "
                "Brief's day-resolution split (H1=Jan-Apr13/H2=Apr14-Apr28) would "
                "yield H2 n=0 in this dataset (cands_with_regime.jsonl extends only "
                "to 2026-04-10) and is non-canonical for the GTOS H1->H2 framing."
            ),
        },
        "config": {
            "sigma_mult_clip": SIGMA_MULT_CLIP,
            "bootstrap_B": args.bootstrap_B,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "threshold_for_verdict": args.threshold,
            "literature_haircut": 0.5,
        },
        "h1_baseline": h1_summary,
        "h2_observed": {
            "pooled": h2_summary,
            "pre_fa2": h2_pre_summary,
            "post_fa2": h2_post_summary,
        },
        "decomposition": {
            "pooled_h2": pooled,
            "pre_fa2_h2": pre_decomp,
            "post_fa2_h2": post_decomp,
        },
        "vol_managed_recovery_estimate": {
            "pooled_h2": pooled_recovery,
            "pre_fa2_h2": pre_recovery,
            "post_fa2_h2": post_recovery,
        },
        "attribution_pct_of_decay": {
            "pooled_move_mag_pct": move_mag_pct,
            "pre_fa2_move_mag_pct": pre_move_mag_pct,
            "post_fa2_move_mag_pct": post_move_mag_pct,
        },
        "bootstrap_ci": bootstrap,
        "q1_4_priority_verdict": verdict,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"[NA8] Wrote {out_path}")

    # Console summary
    print("\n=== NA8 SUMMARY ===")
    print(f"H1 mean R     : {pooled['h1_actual_mean_R']:+.4f} (n={pooled['h1_n']})")
    print(f"H2 mean R     : {pooled['h2_actual_mean_R']:+.4f} (n={pooled['h2_n']})")
    print(f"Total decay   : {pooled['total_decay_R']:+.4f} R/trade")
    print(f"Move-mag      : {pooled['move_magnitude_R']:+.4f} R ({move_mag_pct:.1%} of total)")
    print(f"Signal-trans  : {pooled['signal_translation_R']:+.4f} R")
    print(f"Cross term    : {pooled['cross_term_R']:+.4f} R")
    print(f"Diversification: {pooled['diversification_R']:+.4f} R")
    print(f"Sum check err : {pooled['closure_error_R']:+.6f} R (should be ~0)")
    print(f"\nLit recovery  : {pooled_recovery['literature_recovery_R']:+.4f} R "
          f"({pooled_recovery['literature_recovery_pct_of_decay']:.1%} of decay)")
    print(f"Post-haircut  : {pooled_recovery['post_haircut_recovery_R']:+.4f} R "
          f"({pooled_recovery['post_haircut_pct_of_decay']:.1%} of decay)")

    print(f"\nBootstrap (B={args.bootstrap_B}):")
    bs = bootstrap["move_mag_pct_of_decay"]
    print(f"  move_mag_pct: mean={bs['mean']:.3f}, 95%CI=[{bs['ci_low']:.3f},{bs['ci_high']:.3f}]")

    print(f"\n=== Q1.4 PRIORITY VERDICT ===")
    print(f"Threshold: {verdict['threshold']:.0%}")
    print(f"VERDICT: {verdict['verdict']}")
    print(f"Rationale: {verdict['rationale']}")
    if verdict.get("ci_overlaps_threshold"):
        print(f"NOTE: 95% CI [{verdict['move_mag_pct_ci_95'][0]:.3f},{verdict['move_mag_pct_ci_95'][1]:.3f}] overlaps threshold; verdict is statistically borderline.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
