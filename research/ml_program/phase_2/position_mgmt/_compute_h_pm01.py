"""H-PM01 — Vol-conditional position sizing (Barroso-Santa-Clara 2015 port).

Pre-flight caveat (Agent G NA8 sensitivity, 2026-04-29):
    Vol-managed sizing is structurally negative-EV on the H2 XAUUSD LONG cohort
    specifically (recovery -1.0% point at H2 vol_rank=0.67). H-PM01 must test on the
    BROADER cohort (all instruments + both directions + both H1/H2 + 2022-2023 backfill)
    to determine whether Barroso-Santa-Clara delivers Sharpe lift in general.

Cohort:
    Union of (a) Q1.3 v2 cohort `research/ml_program/models/k54_v1_features_full.csv`
    (n=582 pre-dedup, n=528 post-dedup, 2024-04..2026-04) AND (b) 2022-2023 mechanical
    backfill `data/historical_2022_2023/trade_cohort.csv` (n=1798, 2022-01..2024-02).
    Post-dedup target n ≈ 2,326. Each row has realized_r and date_iso.

Methodology:
    1. Realized vol per trade = rolling 30-day H1 ATR-equivalent (close-to-close log
       return std × sqrt(annualization)) for the instrument at trade entry time.
    2. Compute realized_vol_rank (cross-sectional percentile within instrument) using
       the FULL H1 history of that instrument (no leakage — the rank uses the full
       sample instrument-wide which is exogenous to any single trade outcome and
       constitutes a "regime label", not a feature predicting forward returns).
    3. BSC sigma multiplier = clip(median_vol / realized_vol_30d, 0.5, 2.0).
       Implements Barroso-Santa-Clara 2015 inverse-realized-vol scaling.
    4. Apply multiplier to baseline 2.0% (S79 uniform_fn) → vol-managed R per trade
       = realized_r × bsc_sigma_mult.
    5. Backtest across full union cohort.
    6. Per-cohort breakdown: per-instrument × per-direction × per-period (H1/H2/backfill).
    7. Babu-Hoffman-Levine 2020 attribution of (h2 - h1 mean R) per cohort.
    8. Stationary block bootstrap (Politis-Romano) for SE; DSR-corrected p.

Promotion gate:
    PASS if either:
       (a) ≥+0.10R/trade vs uniform_fn 2.0% on Q1.4 cohort backtest at DSR-p < 0.05.
       (b) ≥+15% Sharpe lift + DD-depth ≤ baseline.
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ============================================================================
# Configuration
# ============================================================================

REPO = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = REPO / "research" / "ml_program" / "phase_2" / "position_mgmt"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Cohort sources
Q13_COHORT = REPO / "research" / "ml_program" / "models" / "k54_v1_features_full.csv"
BACKFILL_COHORT = REPO / "data" / "historical_2022_2023" / "trade_cohort.csv"

# H1 OHLCV sources (we use H1 not H4 — spec says "rolling 30-day H1 ATR")
H1_SOURCES = {
    # symbol -> list of (start_date_excl_after, csv_path)
    # Layered earliest-first; we concat earliest-to-latest
    "XAUUSD": [REPO / "data" / "historical_2022_2023" / "XAUUSD_H1.csv",
               REPO / "data" / "historical" / "XAUUSD_H1.csv",
               REPO / "data" / "historical_2026" / "XAUUSD_H1.csv"],
    "XAGUSD": [REPO / "data" / "historical_2022_2023" / "XAGUSD_H1.csv",
               REPO / "data" / "historical_2026" / "XAGUSD_H1.csv"],
    "USDJPY": [REPO / "data" / "historical_2022_2023" / "USDJPY_H1.csv",
               REPO / "data" / "historical" / "USDJPY_H1.csv",
               REPO / "data" / "historical_2026" / "USDJPY_H1.csv"],
    "GBPUSD": [REPO / "data" / "historical_2022_2023" / "GBPUSD_H1.csv",
               REPO / "data" / "historical" / "GBPUSD_H1.csv",
               REPO / "data" / "historical_2026" / "GBPUSD_H1.csv"],
    "GBPJPY": [REPO / "data" / "historical" / "GBPJPY_H1.csv",
               REPO / "data" / "historical_2026" / "GBPJPY_H1.csv"],
    "NAS100": [REPO / "data" / "historical_2022_2023" / "NAS100_H1.csv",
               REPO / "data" / "historical_2026" / "NAS100_H1.csv"],
    "US30_cash": [REPO / "data" / "historical" / "US30_cash_H1.csv",
                  REPO / "data" / "historical_2026" / "US30_cash_H1.csv"],
    # Symbol-name normalization handled below
}

# H1 trading hours per year for annualization
TRADING_HOURS_PER_YEAR = 24 * 5 * 50  # ~6000 H1 bars/year for FX/Gold; keep ratio
# Realized-vol rolling window in H1 bars (30 days * 24 hours = 720 H1 bars)
ROLLING_VOL_BARS = 30 * 24  # 720 H1 bars

# BSC clip per spec
SIGMA_MULT_CLIP = (0.5, 2.0)

# Cohort definitions (period split)
H1_2026_MONTHS = {"2026-01", "2026-02"}
H2_2026_MONTHS = {"2026-03", "2026-04"}
BACKFILL_DATE_END = pd.Timestamp("2024-02-29T00:00:00Z", tz="UTC")
Q13_DATE_START = pd.Timestamp("2024-03-01T00:00:00Z", tz="UTC")

# Bootstrap config
N_BOOTSTRAP = 1000
BLOCK_LEN = 5  # Politis-Romano stationary block bootstrap; geometric block length = 5 trades
RNG_SEED = 17


# ============================================================================
# Data loading
# ============================================================================


def _normalize_symbol(s: str) -> str:
    """Normalize symbol names across cohorts."""
    s = s.strip().upper()
    if s == "US30_CASH":
        return "US30_cash"
    return s


def load_cohort() -> pd.DataFrame:
    """Load union cohort: Q1.3 v2 (k54_v1_features_full) + 2022-2023 backfill.

    Returns DataFrame with columns:
        trade_id, source, ts (UTC tz-aware), symbol, direction (LONG|SHORT),
        kill_zone, regime_tag, realized_r, period (backfill|H1_2026|H2_2026|Q13_other),
        side (LONG|SHORT alias of direction), framework
    """
    rows = []

    # 1. Q1.3 v2 cohort (n=582 raw, dedup'd to ~528)
    df_q13 = pd.read_csv(Q13_COHORT)
    df_q13 = df_q13.drop_duplicates(subset="trade_id").reset_index(drop=True)
    for _, r in df_q13.iterrows():
        ts_raw = r["date_iso"]
        if not isinstance(ts_raw, str):
            continue
        try:
            # date_iso may be 'YYYY-MM-DD' (unified_csv) or full ISO8601
            if "T" in ts_raw:
                ts = pd.Timestamp(ts_raw).tz_convert("UTC")
            else:
                # Date only — use 12:00 UTC midpoint
                ts = pd.Timestamp(f"{ts_raw}T12:00:00Z")
        except Exception:
            continue
        sym = _normalize_symbol(r["symbol"])
        rows.append({
            "trade_id": r["trade_id"],
            "source": r["source"],
            "ts": ts,
            "symbol": sym,
            "direction": r["direction_long_short"].upper(),
            "kill_zone": r.get("kill_zone"),
            "regime_tag": r.get("regime_tag"),
            "realized_r": float(r["realized_r"]),
            "framework": r.get("framework"),
            "cohort_origin": "q13_v2",
        })

    # 2. 2022-2023 backfill cohort (n=1798, all f11_mechanical)
    df_bf = pd.read_csv(BACKFILL_COHORT)
    for _, r in df_bf.iterrows():
        ts = pd.Timestamp(r["date_iso"])
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        sym = _normalize_symbol(r["symbol"])
        rows.append({
            "trade_id": r["trade_id"],
            "source": r["source"],
            "ts": ts,
            "symbol": sym,
            "direction": r["direction_long_short"].upper(),
            "kill_zone": r.get("kill_zone"),
            "regime_tag": r.get("regime_tag"),
            "realized_r": float(r["realized_r"]),
            "framework": r.get("framework"),
            "cohort_origin": "backfill_2022_2023",
        })

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="trade_id").reset_index(drop=True)
    df = df.sort_values("ts").reset_index(drop=True)
    df["side"] = df["direction"]

    # Period assignment
    df["period_month"] = df["ts"].dt.strftime("%Y-%m")
    df["period"] = "other"
    df.loc[df["period_month"].isin(H1_2026_MONTHS), "period"] = "H1_2026"
    df.loc[df["period_month"].isin(H2_2026_MONTHS), "period"] = "H2_2026"
    df.loc[df["ts"] < BACKFILL_DATE_END, "period"] = "backfill_2022_2023"
    df.loc[(df["ts"] >= Q13_DATE_START) & (df["period"] == "other"), "period"] = "Q13_2024_2025"

    return df


def load_h1(symbol: str) -> pd.DataFrame:
    """Load H1 OHLCV (concatenated across data sources), compute realized vol + rank."""
    paths = H1_SOURCES.get(symbol, [])
    if not paths:
        return pd.DataFrame()
    parts = []
    for p in paths:
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        df["time"] = pd.to_datetime(df["time"], utc=True)
        parts.append(df)
    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out = out.drop_duplicates(subset="time").sort_values("time").reset_index(drop=True)

    # Rolling 30-day vol = log return std over 720 H1 bars * sqrt(annualization)
    out["log_ret"] = np.log(out["close"] / out["close"].shift(1))
    out["realized_vol_30d"] = out["log_ret"].rolling(ROLLING_VOL_BARS).std() * np.sqrt(TRADING_HOURS_PER_YEAR)

    # Cross-sectional rank within instrument (entire history)
    out["realized_vol_rank"] = out["realized_vol_30d"].rank(pct=True)

    # Barroso multiplier: median_vol / realized_vol_30d, clipped
    median_vol = out["realized_vol_30d"].median()
    out["bsc_sigma_mult"] = (median_vol / out["realized_vol_30d"]).clip(*SIGMA_MULT_CLIP)
    out["instrument_median_vol"] = median_vol
    return out


def attach_vol(trades: pd.DataFrame) -> pd.DataFrame:
    """Join trade rows with the most-recent prior H1 realized-vol/rank/multiplier."""
    out_rows = []
    h1_cache: dict[str, pd.DataFrame] = {}
    for sym in trades["symbol"].unique():
        h1 = load_h1(sym)
        if len(h1) == 0:
            print(f"  WARN: no H1 data for {sym} — skipping {len(trades[trades['symbol']==sym])} trades")
            continue
        h1_cache[sym] = h1

    for sym, sub in trades.groupby("symbol"):
        if sym not in h1_cache:
            continue
        h1 = h1_cache[sym]
        h1_idx = h1.set_index("time").sort_index()
        for _, t in sub.iterrows():
            ts = t["ts"]
            idx = h1_idx.index.searchsorted(ts, side="right") - 1
            if idx < 0 or idx >= len(h1_idx):
                continue
            row = h1_idx.iloc[idx]
            rv = row["realized_vol_30d"]
            rk = row["realized_vol_rank"]
            mult = row["bsc_sigma_mult"]
            if pd.isna(rv) or pd.isna(mult):
                continue
            out_rows.append({
                **t.to_dict(),
                "realized_vol_30d": float(rv),
                "realized_vol_rank": float(rk),
                "bsc_sigma_mult": float(mult),
                "instrument_median_vol": float(row["instrument_median_vol"]),
            })
    out = pd.DataFrame(out_rows)
    if len(out) > 0:
        out = out.sort_values("ts").reset_index(drop=True)
    return out


# ============================================================================
# Vol-managed backtest
# ============================================================================


def vm_backtest(df: pd.DataFrame) -> dict[str, Any]:
    """Apply BSC vol-managed multiplier to baseline 2% sizing.

    baseline_R = realized_r (already in R-multiples; baseline sizing is implicit 2.0% per S79).
    vol_managed_R = realized_r × bsc_sigma_mult

    R-multiples are unit-less; multiplier scales risk-per-trade. So multiplied-R IS the
    realized R when using vol-managed sizing instead of uniform sizing. This is the
    canonical Barroso-Santa-Clara port (Sharpe 0.53→0.97 in their paper).

    NOTE: This treats the multiplier as a sizing scalar. Total exposure must be checked
    against MTM-DD constraints separately (see DD/Sharpe analysis).
    """
    df = df.dropna(subset=["realized_r", "bsc_sigma_mult"]).copy()
    df["baseline_r"] = df["realized_r"]
    df["vm_r"] = df["realized_r"] * df["bsc_sigma_mult"]

    n = len(df)
    if n == 0:
        return {"_error": "empty cohort"}

    base_mean = float(df["baseline_r"].mean())
    base_std = float(df["baseline_r"].std(ddof=1)) if n > 1 else float("nan")
    vm_mean = float(df["vm_r"].mean())
    vm_std = float(df["vm_r"].std(ddof=1)) if n > 1 else float("nan")

    # Sharpe = mean / std (per-trade Sharpe; not annualized)
    base_sharpe = base_mean / base_std if base_std and base_std > 0 else float("nan")
    vm_sharpe = vm_mean / vm_std if vm_std and vm_std > 0 else float("nan")

    # Win rate
    base_wr = float((df["baseline_r"] > 0).mean())
    vm_wr = float((df["vm_r"] > 0).mean())

    # Equity curve & DD
    base_eq = df["baseline_r"].cumsum()
    vm_eq = df["vm_r"].cumsum()
    base_dd = float((base_eq - base_eq.cummax()).min())
    vm_dd = float((vm_eq - vm_eq.cummax()).min())
    base_terminal = float(base_eq.iloc[-1])
    vm_terminal = float(vm_eq.iloc[-1])

    return {
        "n_trades": int(n),
        "baseline": {
            "mean_r": base_mean,
            "std_r": base_std,
            "sharpe": base_sharpe,
            "wr": base_wr,
            "max_dd_r": base_dd,
            "terminal_r": base_terminal,
        },
        "vol_managed": {
            "mean_r": vm_mean,
            "std_r": vm_std,
            "sharpe": vm_sharpe,
            "wr": vm_wr,
            "max_dd_r": vm_dd,
            "terminal_r": vm_terminal,
        },
        "delta": {
            "mean_r": vm_mean - base_mean,
            "sharpe": vm_sharpe - base_sharpe if math.isfinite(vm_sharpe) and math.isfinite(base_sharpe) else float("nan"),
            "sharpe_pct": (vm_sharpe / base_sharpe - 1.0) * 100 if math.isfinite(vm_sharpe) and math.isfinite(base_sharpe) and base_sharpe != 0 else float("nan"),
            "wr_pp": (vm_wr - base_wr) * 100,
            "max_dd_r": vm_dd - base_dd,
            "terminal_r": vm_terminal - base_terminal,
        },
    }


# ============================================================================
# Politis-Romano stationary block bootstrap + DSR
# ============================================================================


def stationary_block_bootstrap(
    paired: np.ndarray,
    n_boot: int = 1000,
    block_len: float = 5.0,
    seed: int = 17,
) -> dict[str, float]:
    """Politis-Romano 1994 stationary block bootstrap of paired difference (vm_r - base_r).

    Returns mean, std, 95% CI, p-value of mean=0 (two-sided).
    """
    rng = np.random.default_rng(seed)
    n = len(paired)
    p_geom = 1.0 / block_len  # geometric block length distribution
    means = np.empty(n_boot)
    for b in range(n_boot):
        # Sample blocks until we fill n observations
        idxs = []
        while len(idxs) < n:
            start = rng.integers(0, n)
            block_size = rng.geometric(p_geom)
            for k in range(block_size):
                if len(idxs) >= n:
                    break
                idxs.append((start + k) % n)
        means[b] = paired[idxs].mean()
    boot_mean = float(np.mean(means))
    boot_std = float(np.std(means, ddof=1))
    ci_lo = float(np.percentile(means, 2.5))
    ci_hi = float(np.percentile(means, 97.5))
    # Two-sided p-value of H0: paired_mean = 0
    obs_mean = float(paired.mean())
    null_means = means - boot_mean  # center under null
    p_two = float(2 * min(np.mean(null_means >= abs(obs_mean)), np.mean(null_means <= -abs(obs_mean))))
    p_two = max(p_two, 1.0 / n_boot)
    return {
        "obs_paired_mean": obs_mean,
        "boot_mean": boot_mean,
        "boot_std": boot_std,
        "ci_95_lo": ci_lo,
        "ci_95_hi": ci_hi,
        "p_two_sided": p_two,
    }


def deflated_sharpe_ratio(
    sr_observed: float,
    n_trades: int,
    n_trials: int,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> dict[str, float]:
    """Bailey-Lopez de Prado 2014 Deflated Sharpe Ratio.

    Returns DSR-adjusted z and p-value of "true SR > 0" given trial population.
    """
    if not math.isfinite(sr_observed) or n_trades <= 1:
        return {"dsr_z": float("nan"), "dsr_p": float("nan")}

    # Expected max SR under null with n_trials independent SR estimates
    # E[SR_max] = sqrt(2 * ln(n_trials)) for Gaussian
    em_max = math.sqrt(2 * math.log(n_trials)) if n_trials > 1 else 0.0

    # Standard error of observed SR (Mertens 2002)
    se_sr = math.sqrt(
        (1 + 0.5 * sr_observed**2 - skew * sr_observed + (kurt - 3) / 4 * sr_observed**2) / max(1, n_trades - 1)
    )
    if se_sr <= 0 or not math.isfinite(se_sr):
        return {"dsr_z": float("nan"), "dsr_p": float("nan")}

    z = (sr_observed - em_max * se_sr) / se_sr
    # One-sided p (true SR > 0 after deflation)
    from math import erf
    p = 0.5 * (1 - erf(z / math.sqrt(2)))
    return {
        "dsr_z": float(z),
        "dsr_p": float(p),
        "expected_max_sr_under_null": float(em_max * se_sr),
        "se_sr": float(se_sr),
        "n_trials_assumed": int(n_trials),
    }


# ============================================================================
# Babu-Hoffman-Levine 2020 attribution
# ============================================================================


def babu_decompose(
    h1: pd.DataFrame, h2: pd.DataFrame, x_col: str = "bsc_sigma_mult", y_col: str = "realized_r"
) -> dict[str, float]:
    if len(h1) == 0 or len(h2) == 0:
        return {"_note": f"empty cohort h1_n={len(h1)} h2_n={len(h2)}"}
    x1, y1 = h1[x_col].values, h1[y_col].values
    x2, y2 = h2[x_col].values, h2[y_col].values
    e_x1, e_x2 = float(np.mean(x1)), float(np.mean(x2))
    e_y1, e_y2 = float(np.mean(y1)), float(np.mean(y2))
    h1_actual = e_y1
    h2_actual = e_y2
    total_decay = h2_actual - h1_actual
    move_mag = (e_x2 - e_x1) * e_y1
    signal_trans = e_x1 * (e_y2 - e_y1)
    cross_term = (e_x2 - e_x1) * (e_y2 - e_y1)
    diversification = total_decay - (move_mag + signal_trans + cross_term)
    if abs(total_decay) > 1e-12:
        move_mag_pct = move_mag / abs(total_decay)
        signal_trans_pct = signal_trans / abs(total_decay)
    else:
        move_mag_pct = 0.0
        signal_trans_pct = 0.0
    return {
        "h1_n": int(len(h1)),
        "h2_n": int(len(h2)),
        "h1_mean_R": h1_actual,
        "h2_mean_R": h2_actual,
        "total_decay_R": total_decay,
        "move_magnitude_R": move_mag,
        "signal_translation_R": signal_trans,
        "cross_term_R": cross_term,
        "diversification_R": diversification,
        "move_mag_pct_of_decay": move_mag_pct,
        "signal_trans_pct_of_decay": signal_trans_pct,
    }


# ============================================================================
# Promotion gate evaluation
# ============================================================================


def evaluate_gate(result: dict, dsr: dict, gate_thresh_R: float = 0.10, gate_thresh_sharpe_pct: float = 15.0) -> dict:
    delta_mean = result.get("delta", {}).get("mean_r", float("nan"))
    delta_sharpe_pct = result.get("delta", {}).get("sharpe_pct", float("nan"))
    delta_dd = result.get("delta", {}).get("max_dd_r", float("nan"))
    dsr_p = dsr.get("dsr_p", float("nan"))

    # Path A: ≥+0.10R/trade vs uniform_fn 2.0% on Q1.4 cohort backtest at DSR-p<0.05.
    path_a_pass = (
        math.isfinite(delta_mean)
        and delta_mean >= gate_thresh_R
        and math.isfinite(dsr_p)
        and dsr_p < 0.05
    )
    # Path B: ≥+15% Sharpe lift + DD-depth ≤ baseline (i.e. delta_dd >= 0).
    path_b_pass = (
        math.isfinite(delta_sharpe_pct)
        and delta_sharpe_pct >= gate_thresh_sharpe_pct
        and math.isfinite(delta_dd)
        and delta_dd >= 0.0
    )
    return {
        "path_a_R_lift_pass": bool(path_a_pass),
        "path_b_sharpe_lift_pass": bool(path_b_pass),
        "overall_pass": bool(path_a_pass or path_b_pass),
        "details": {
            "delta_mean_r": delta_mean,
            "gate_thresh_R": gate_thresh_R,
            "dsr_p": dsr_p,
            "delta_sharpe_pct": delta_sharpe_pct,
            "gate_thresh_sharpe_pct": gate_thresh_sharpe_pct,
            "delta_dd_r": delta_dd,
        },
    }


# ============================================================================
# Main
# ============================================================================


def run() -> None:
    print("=" * 80)
    print("H-PM01 — Vol-conditional position sizing (Barroso-Santa-Clara port)")
    print("=" * 80)
    print()
    print("Loading cohort...")
    trades = load_cohort()
    print(f"  Raw cohort: n={len(trades)}")
    print(f"  By origin: {trades['cohort_origin'].value_counts().to_dict()}")
    print(f"  By symbol: {trades['symbol'].value_counts().to_dict()}")
    print(f"  By direction: {trades['direction'].value_counts().to_dict()}")
    print(f"  By period: {trades['period'].value_counts().to_dict()}")
    print()

    print("Attaching realized vol + Barroso multiplier from H1 OHLCV...")
    df = attach_vol(trades)
    print(f"  After attach: n={len(df)} (dropped {len(trades) - len(df)} for missing H1 data)")
    print()

    if len(df) == 0:
        print("ERROR: empty cohort post-vol-attach. Aborting.")
        sys.exit(1)

    # Save enriched cohort for inspection
    df.to_parquet(OUT_DIR / "_enriched_cohort.parquet", index=False)
    df.to_csv(OUT_DIR / "_enriched_cohort.csv", index=False)
    print(f"  Saved enriched cohort: {OUT_DIR / '_enriched_cohort.csv'}")
    print()

    # ============================================================================
    # PRIMARY: Q1.4 full-cohort backtest
    # ============================================================================
    print("=" * 80)
    print("PRIMARY: Q1.4 full-cohort backtest")
    print("=" * 80)
    full_result = vm_backtest(df)
    paired = (df["realized_r"] * df["bsc_sigma_mult"] - df["realized_r"]).values
    full_boot = stationary_block_bootstrap(paired, n_boot=N_BOOTSTRAP, block_len=BLOCK_LEN, seed=RNG_SEED)
    # DSR on the LEVEL Sharpe of vol-managed system (descriptive)
    full_dsr_level = deflated_sharpe_ratio(
        sr_observed=full_result["vol_managed"]["sharpe"],
        n_trades=full_result["n_trades"],
        n_trials=200,  # per pre-registered N=200-500 trial budget
        skew=float(pd.Series(df["realized_r"] * df["bsc_sigma_mult"]).skew()),
        kurt=float(pd.Series(df["realized_r"] * df["bsc_sigma_mult"]).kurtosis() + 3),
    )
    # PRIMARY: DSR on PAIRED-DELTA Sharpe (the actual test for "vol-managed beats baseline")
    paired_sr = float(np.mean(paired) / np.std(paired, ddof=1)) if np.std(paired, ddof=1) > 0 else float("nan")
    paired_skew = float(pd.Series(paired).skew())
    paired_kurt = float(pd.Series(paired).kurtosis() + 3)
    full_dsr = deflated_sharpe_ratio(
        sr_observed=paired_sr,
        n_trades=full_result["n_trades"],
        n_trials=200,
        skew=paired_skew,
        kurt=paired_kurt,
    )
    full_dsr["paired_delta_sr"] = paired_sr
    full_dsr["paired_skew"] = paired_skew
    full_dsr["paired_excess_kurt"] = paired_kurt - 3
    full_gate = evaluate_gate(full_result, full_dsr)
    print(f"  n = {full_result['n_trades']}")
    print(f"  Baseline mean R = {full_result['baseline']['mean_r']:.4f}, Sharpe = {full_result['baseline']['sharpe']:.4f}")
    print(f"  Vol-managed mean R = {full_result['vol_managed']['mean_r']:.4f}, Sharpe = {full_result['vol_managed']['sharpe']:.4f}")
    print(f"  Delta mean R = {full_result['delta']['mean_r']:.4f}")
    print(f"  Delta Sharpe = {full_result['delta']['sharpe']:.4f} ({full_result['delta']['sharpe_pct']:.2f}%)")
    print(f"  Bootstrap CI95 of paired delta R: [{full_boot['ci_95_lo']:.4f}, {full_boot['ci_95_hi']:.4f}]")
    print(f"  Bootstrap p (paired mean = 0): {full_boot['p_two_sided']:.4f}")
    print(f"  Paired delta SR: {full_dsr['paired_delta_sr']:.4f} (skew={full_dsr['paired_skew']:.2f}, exc_kurt={full_dsr['paired_excess_kurt']:.2f})")
    print(f"  DSR z (paired delta) = {full_dsr['dsr_z']:.3f}, DSR p = {full_dsr['dsr_p']:.4f} (n_trials=200)")
    print(f"  DSR (descriptive, vol-managed system Sharpe): z = {full_dsr_level['dsr_z']:.3f}, p = {full_dsr_level['dsr_p']:.4f}")
    print(f"  Gate verdict: {'PASS' if full_gate['overall_pass'] else 'FAIL'}")
    print(f"    Path A (R lift >=+0.10 & DSR-p<0.05): {full_gate['path_a_R_lift_pass']}")
    print(f"    Path B (Sharpe >=+15% & DD<=baseline): {full_gate['path_b_sharpe_lift_pass']}")
    print()

    # ============================================================================
    # PER-COHORT: instrument × direction × period
    # ============================================================================
    print("=" * 80)
    print("PER-COHORT BREAKDOWN")
    print("=" * 80)

    per_cohort = {}

    # Per-instrument
    print()
    print("[per-instrument]")
    per_cohort["per_instrument"] = {}
    for sym, sub in df.groupby("symbol"):
        if len(sub) < 10:
            continue
        r = vm_backtest(sub)
        paired_sub = (sub["realized_r"] * sub["bsc_sigma_mult"] - sub["realized_r"]).values
        boot_sub = stationary_block_bootstrap(paired_sub, n_boot=N_BOOTSTRAP, block_len=BLOCK_LEN, seed=RNG_SEED + 1)
        # Per-instrument paired-delta DSR
        ps = pd.Series(paired_sub)
        if ps.std(ddof=1) > 0:
            sr_p = float(ps.mean() / ps.std(ddof=1))
            dsr_p = deflated_sharpe_ratio(
                sr_observed=sr_p, n_trades=len(paired_sub), n_trials=50,  # per-instrument lower trial budget
                skew=float(ps.skew()), kurt=float(ps.kurtosis() + 3),
            )
        else:
            dsr_p = {"dsr_z": float("nan"), "dsr_p": float("nan")}
        per_cohort["per_instrument"][sym] = {"backtest": r, "bootstrap": boot_sub, "dsr_paired": dsr_p}
        print(f"  {sym:10s}  n={r['n_trades']:>4d}  delta_R={r['delta']['mean_r']:+.4f}  delta_Sharpe={r['delta']['sharpe']:+.4f}  delta_Sharpe%={r['delta']['sharpe_pct']:+.2f}%  delta_DD={r['delta']['max_dd_r']:+.2f}R  boot_p={boot_sub['p_two_sided']:.4f}  DSR-p={dsr_p.get('dsr_p', float('nan')):.4f}")

    # Per-direction
    print()
    print("[per-direction]")
    per_cohort["per_direction"] = {}
    for d, sub in df.groupby("direction"):
        if len(sub) < 10:
            continue
        r = vm_backtest(sub)
        paired_sub = (sub["realized_r"] * sub["bsc_sigma_mult"] - sub["realized_r"]).values
        boot_sub = stationary_block_bootstrap(paired_sub, n_boot=N_BOOTSTRAP, block_len=BLOCK_LEN, seed=RNG_SEED + 2)
        per_cohort["per_direction"][d] = {"backtest": r, "bootstrap": boot_sub}
        print(f"  {d:6s}  n={r['n_trades']:>4d}  delta_R={r['delta']['mean_r']:+.4f}  delta_Sharpe={r['delta']['sharpe']:+.4f}  delta_Sharpe%={r['delta']['sharpe_pct']:+.2f}%  delta_DD={r['delta']['max_dd_r']:+.2f}R  boot_p={boot_sub['p_two_sided']:.4f}")

    # Per-period
    print()
    print("[per-period]")
    per_cohort["per_period"] = {}
    for p, sub in df.groupby("period"):
        if len(sub) < 10:
            continue
        r = vm_backtest(sub)
        paired_sub = (sub["realized_r"] * sub["bsc_sigma_mult"] - sub["realized_r"]).values
        boot_sub = stationary_block_bootstrap(paired_sub, n_boot=N_BOOTSTRAP, block_len=BLOCK_LEN, seed=RNG_SEED + 3)
        per_cohort["per_period"][p] = {"backtest": r, "bootstrap": boot_sub}
        print(f"  {p:25s}  n={r['n_trades']:>4d}  delta_R={r['delta']['mean_r']:+.4f}  delta_Sharpe={r['delta']['sharpe']:+.4f}  delta_Sharpe%={r['delta']['sharpe_pct']:+.2f}%  delta_DD={r['delta']['max_dd_r']:+.2f}R  boot_p={boot_sub['p_two_sided']:.4f}")

    # Per-instrument × direction
    print()
    print("[per-instrument × direction]")
    per_cohort["per_instrument_direction"] = {}
    for (sym, d), sub in df.groupby(["symbol", "direction"]):
        if len(sub) < 10:
            continue
        r = vm_backtest(sub)
        key = f"{sym}|{d}"
        per_cohort["per_instrument_direction"][key] = {"backtest": r, "n": r["n_trades"]}
        print(f"  {sym:10s} {d:6s}  n={r['n_trades']:>4d}  delta_R={r['delta']['mean_r']:+.4f}  delta_Sharpe%={r['delta']['sharpe_pct']:+.2f}%")

    # ============================================================================
    # AGENT G H2-XAU-LONG CAVEAT REPLICATION
    # ============================================================================
    print()
    print("=" * 80)
    print("AGENT G CAVEAT REPLICATION: H2-2026 XAUUSD LONG cohort (n_expected≈32)")
    print("=" * 80)
    h2_xau_long = df[(df["symbol"] == "XAUUSD") & (df["direction"] == "LONG") & (df["period"] == "H2_2026")]
    if len(h2_xau_long) >= 10:
        r = vm_backtest(h2_xau_long)
        paired_sub = (h2_xau_long["realized_r"] * h2_xau_long["bsc_sigma_mult"] - h2_xau_long["realized_r"]).values
        boot_sub = stationary_block_bootstrap(paired_sub, n_boot=N_BOOTSTRAP, block_len=BLOCK_LEN, seed=RNG_SEED + 99)
        per_cohort["h2_xau_long_caveat"] = {"backtest": r, "bootstrap": boot_sub}
        print(f"  n={r['n_trades']}")
        print(f"  Baseline mean R = {r['baseline']['mean_r']:.4f}")
        print(f"  Vol-managed mean R = {r['vol_managed']['mean_r']:.4f}")
        print(f"  Delta R = {r['delta']['mean_r']:+.4f}  (Agent G predicted ≈ -0.008)")
        print(f"  Bootstrap p: {boot_sub['p_two_sided']:.4f}")
    else:
        print(f"  WARNING: H2 XAU LONG cohort too small (n={len(h2_xau_long)})")
        per_cohort["h2_xau_long_caveat"] = {"_note": f"n={len(h2_xau_long)} too small"}

    # ============================================================================
    # BABU DECOMPOSITION (H1 vs H2 2026 per-instrument)
    # ============================================================================
    print()
    print("=" * 80)
    print("BABU DECOMPOSITION (H1-2026 → H2-2026, per-instrument-direction)")
    print("=" * 80)
    babu_results = {}
    for (sym, d), sub in df.groupby(["symbol", "direction"]):
        h1 = sub[sub["period"] == "H1_2026"]
        h2 = sub[sub["period"] == "H2_2026"]
        if len(h1) < 5 or len(h2) < 5:
            continue
        b = babu_decompose(h1, h2)
        key = f"{sym}|{d}"
        babu_results[key] = b
        if "_note" not in b:
            print(f"  {sym:10s} {d:6s}  H1 n={b['h1_n']:>3d} H2 n={b['h2_n']:>3d}  decay={b['total_decay_R']:+.4f}R  move-mag={b['move_mag_pct_of_decay']*100:+.1f}%  signal-trans={b['signal_trans_pct_of_decay']*100:+.1f}%")

    # ============================================================================
    # SAVE FULL JSON
    # ============================================================================
    out = {
        "metadata": {
            "task": "H-PM01 — Vol-conditional position sizing (Barroso-Santa-Clara port)",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "cohort_size": int(len(df)),
            "cohort_origin_counts": df["cohort_origin"].value_counts().to_dict(),
            "symbols": sorted(df["symbol"].unique().tolist()),
            "directions": sorted(df["direction"].unique().tolist()),
            "periods": sorted(df["period"].unique().tolist()),
            "rolling_vol_bars_h1": ROLLING_VOL_BARS,
            "sigma_mult_clip": list(SIGMA_MULT_CLIP),
            "bootstrap_n": N_BOOTSTRAP,
            "bootstrap_block_len": BLOCK_LEN,
            "rng_seed": RNG_SEED,
        },
        "primary_full_cohort": {
            "backtest": full_result,
            "bootstrap": full_boot,
            "dsr_paired_delta": full_dsr,
            "dsr_level_descriptive": full_dsr_level,
            "gate": full_gate,
        },
        "per_cohort": per_cohort,
        "babu_decomposition_h1_h2_2026": babu_results,
    }

    out_path = OUT_DIR / "h_pm01_per_cohort_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print()
    print(f"  Saved: {out_path}")
    print()
    print("DONE.")


if __name__ == "__main__":
    run()
