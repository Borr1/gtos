#!/usr/bin/env python3
"""
GTOS Variance Ratio Analysis
Lo-MacKinlay (1988) heteroskedasticity-robust variance ratio tests.
Chow-Denning (1993) joint test.

Usage:
    python research/diagnostics/run_variance_ratio.py

Outputs:
    research/diagnostics/variance_ratio_results.json
    research/diagnostics/variance_ratio_summary.md
    research/diagnostics/plots/*.png
"""

import os
import json
import sys
import warnings
from datetime import datetime

# Force UTF-8 output on Windows so arrows/dashes don't crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

# ── matplotlib setup (non-interactive) ──────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
REPO_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR    = os.path.join(REPO_ROOT, "data", "historical")
OUTPUT_DIR  = os.path.dirname(__file__)
PLOTS_DIR   = os.path.join(OUTPUT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
INSTRUMENTS = {
    "XAUUSD": {"prefix": "XAUUSD",    "tfs": ["M1", "M5", "M15", "H1", "H4", "D1"]},
    "US30":   {"prefix": "US30_cash", "tfs": ["M15", "H1", "H4", "D1"]},
    "USDJPY": {"prefix": "USDJPY",    "tfs": ["M15", "H1", "H4", "D1"]},
    "GBPJPY": {"prefix": "GBPJPY",    "tfs": ["M15", "H1", "H4", "D1"]},
    "GBPUSD": {"prefix": "GBPUSD",    "tfs": ["M15", "H1", "H4", "D1"]},
}

# q-period lags
Q_VALUES = [2, 4, 8, 16, 32, 64]

# Minimum observations before running a VR test
MIN_OBS = 200

# Timeframe bar duration in minutes
TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}

# XAUUSD kill zones (UTC hours, half-open interval [lo, hi))
KILL_ZONES = {
    "London":  (7.0, 10.5),
    "NewYork": (13.0, 17.0),
    "All":     None,
}

# bars per month for each timeframe (trading days ~ 21, trading hours ~ 24 for FX/Gold)
BARS_PER_MONTH = {"M1": 9600, "M5": 1920, "M15": 640, "H1": 160, "H4": 40, "D1": 21}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_csv(symbol: str, tf: str) -> pd.DataFrame | None:
    """Return a DataFrame with columns [time, close] or None if file missing."""
    prefix = INSTRUMENTS[symbol]["prefix"]
    path = os.path.join(DATA_DIR, f"{prefix}_{tf}.csv")
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    # Normalise column names — some files have tick_volume/spread/real_volume extras
    if "time" not in df.columns:
        df.columns = ["time", "open", "high", "low", "close"] + list(df.columns[5:])

    df["time"] = pd.to_datetime(df["time"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["time", "close"]).sort_values("time").reset_index(drop=True)
    return df[["time", "close"]]


def compute_log_returns(df: pd.DataFrame, tf: str):
    """
    Return (r, t) where:
      r – numpy array of valid 1-period log returns
      t – numpy array of corresponding timestamps (end of each return interval)

    For intraday timeframes, returns that span overnight/weekend gaps
    (gap > 3× expected bar duration) are discarded.
    """
    closes = df["close"].values.astype(np.float64)
    times  = df["time"].values  # numpy datetime64

    r = np.diff(np.log(closes))        # raw log-returns, length n-1
    t = times[1:]                      # timestamp of the closing bar

    if tf == "D1":
        # Keep all daily returns (overnight gaps are expected)
        valid = np.isfinite(r)
    else:
        expected_min = TF_MINUTES[tf]
        gaps_min = df["time"].diff().dt.total_seconds().iloc[1:].values / 60
        # gap[i] = time from bar i to bar i+1
        valid = (gaps_min <= expected_min * 3) & np.isfinite(r)

    return r[valid], t[valid]


# ─────────────────────────────────────────────────────────────────────────────
# LO-MACKINLAY (1988) VARIANCE RATIO TEST
# ─────────────────────────────────────────────────────────────────────────────

def vr_lm(r: np.ndarray, q: int):
    """
    Compute Lo-MacKinlay (1988) heteroskedasticity-robust variance ratio.

    Returns (VR, z_star, p_star, z_homo, p_homo) or None if n is too small.

    VR(q) = Var(q-period overlapping returns) / (q × Var(1-period returns))

    Under the random-walk null: VR → 1.
    VR > 1 → positive autocorrelation (momentum).
    VR < 1 → negative autocorrelation (mean-reversion).

    z_star  uses the heteroskedasticity-consistent asymptotic variance
            (Lo-MacKinlay 1988, eq. 17).
    z_homo  uses the homoskedastic asymptotic variance
            (Lo-MacKinlay 1988, eq. 14).
    Both z-statistics are asymptotically N(0,1) under H0.
    """
    T = len(r)
    if T < max(q * 4, MIN_OBS):
        return None

    mu = r.mean()
    u  = r - mu                                    # demeaned 1-period returns

    # ── 1-period variance (unbiased) ────────────────────────────────────────
    sigma1_sq = np.dot(u, u) / (T - 1)
    if sigma1_sq < 1e-15:
        return None

    # ── q-period overlapping returns ─────────────────────────────────────────
    r_q   = np.convolve(r, np.ones(q, dtype=np.float64), "valid")  # length T-q+1
    u_q   = r_q - q * mu
    T_q   = len(r_q)

    sigma_q_sq = np.dot(u_q, u_q) / (T_q - 1)    # unbiased q-period variance

    # ── Variance Ratio ───────────────────────────────────────────────────────
    VR = sigma_q_sq / (q * sigma1_sq)

    # ── Heteroskedastic-robust asymptotic variance (theta*) ─────────────────
    # δ̂(j) = T × [Σ_t u_t² u_{t-j}²] / [Σ_t u_t²]²   (Lo-MacKinlay 1988, eq.17)
    # θ*(q) = Σ_{j=1}^{q-1} [2(q-j)/q]² × δ̂(j)
    sum_u2  = np.dot(u, u)                        # Σ u_t²
    denom2  = sum_u2 ** 2                         # (Σ u_t²)²

    theta_star = 0.0
    for j in range(1, q):
        cross = np.dot(u[j:] ** 2, u[:T - j] ** 2)
        delta_j = T * cross / denom2
        w_j = (2.0 * (q - j) / q) ** 2
        theta_star += w_j * delta_j

    if theta_star <= 0:
        return None

    # ── z-statistics ────────────────────────────────────────────────────────
    z_star = np.sqrt(T) * (VR - 1.0) / np.sqrt(theta_star)
    theta_homo = 2.0 * (2 * q - 1) * (q - 1) / (3.0 * q)
    z_homo = np.sqrt(T) * (VR - 1.0) / np.sqrt(theta_homo)

    p_star = float(2.0 * stats.norm.sf(abs(z_star)))
    p_homo = float(2.0 * stats.norm.sf(abs(z_homo)))

    return float(VR), float(z_star), p_star, float(z_homo), p_homo


# ─────────────────────────────────────────────────────────────────────────────
# CHOW-DENNING (1993) JOINT TEST
# ─────────────────────────────────────────────────────────────────────────────

def chow_denning(r: np.ndarray, q_values: list[int]) -> dict | None:
    """
    Chow-Denning (1993) joint variance ratio test.

    H0: VR(q) = 1 for ALL q in q_values simultaneously.

    CD statistic = max |z*(q_j)|.
    p-value: Bonferroni upper bound = min(1, m × min_p), where m = #q values tested.
    (Conservative — the exact SMM critical values are not available in scipy.)
    """
    pairs = []
    for q in q_values:
        res = vr_lm(r, q)
        if res is not None:
            pairs.append((q, res[1], res[2]))      # (q, z_star, p_star)

    if not pairs:
        return None

    abs_zs  = [abs(p[1]) for p in pairs]
    max_idx = int(np.argmax(abs_zs))
    m       = len(pairs)
    min_p   = min(p[2] for p in pairs)

    return {
        "max_z_abs":        round(float(abs_zs[max_idx]), 4),
        "q_at_max_z":       int(pairs[max_idx][0]),
        "p_bonferroni":     round(float(min(1.0, m * min_p)), 6),
        "n_q_tested":       m,
        "min_individual_p": round(float(min_p), 6),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def classify(vr, p_value) -> str:
    if vr is None or p_value is None or not np.isfinite(p_value):
        return "N/A"
    if p_value >= 0.10:
        return "RANDOM_WALK"
    direction = "MOMENTUM" if vr > 1.0 else "MEAN_REVERSION"
    if p_value < 0.01:
        strength = "STRONG"
    elif p_value < 0.05:
        strength = "MODERATE"
    else:
        strength = "SUGGESTIVE"
    return f"{direction}_{strength}"


# ─────────────────────────────────────────────────────────────────────────────
# ROLLING VR
# ─────────────────────────────────────────────────────────────────────────────

def rolling_vr(r: np.ndarray, t: np.ndarray, q: int = 8, tf: str = "H1"):
    """
    Compute rolling VR(q) over a 6-month window, stepped monthly.
    Returns (vr_series, date_series) or (None, None) if insufficient data.
    """
    window = BARS_PER_MONTH.get(tf, 160) * 6
    if len(r) < int(window * 1.5):
        return None, None

    step  = max(1, BARS_PER_MONTH.get(tf, 160))   # ~1 month step
    vrs, dates = [], []

    for start in range(0, len(r) - window + 1, step):
        chunk = r[start : start + window]
        res   = vr_lm(chunk, q)
        if res is not None:
            vrs.append(res[0])
            # Use the midpoint timestamp
            mid = (start + window // 2)
            if mid < len(t):
                dates.append(pd.Timestamp(t[mid]))
            else:
                dates.append(pd.Timestamp(t[-1]))

    if len(vrs) < 3:
        return None, None
    return np.array(vrs, dtype=np.float64), dates


# ─────────────────────────────────────────────────────────────────────────────
# KILL ZONE ANALYSIS  (XAUUSD only)
# ─────────────────────────────────────────────────────────────────────────────

def kill_zone_vr(df: pd.DataFrame) -> dict:
    """
    Run VR analysis on XAUUSD M15 data filtered to each kill zone.

    Within-session returns only: consecutive bars within a calendar date are
    used.  Returns from different sessions on the same day are kept separate
    and then concatenated across all dates.
    """
    dt = pd.to_datetime(df["time"])
    hour_f = dt.dt.hour + dt.dt.minute / 60.0     # fractional UTC hour

    results = {}
    for kz_name, hours in KILL_ZONES.items():
        if hours is None:
            sub = df.copy()
        else:
            lo, hi = hours
            sub = df[((hour_f >= lo) & (hour_f < hi))].reset_index(drop=True)

        if len(sub) < MIN_OBS * 2:
            results[kz_name] = {"error": "insufficient_data", "n_bars": len(sub)}
            continue

        # Compute within-day log returns
        sub_dt  = pd.to_datetime(sub["time"])
        sub_date = sub_dt.dt.date
        all_r = []
        for d in sorted(sub_date.unique()):
            day_closes = sub.loc[sub_date == d, "close"].values.astype(np.float64)
            if len(day_closes) >= 2:
                all_r.extend(np.diff(np.log(day_closes)).tolist())

        r = np.array(all_r)
        r = r[np.isfinite(r)]

        if len(r) < MIN_OBS:
            results[kz_name] = {"error": "insufficient_returns", "n_returns": len(r)}
            continue

        kz_out = {"n_returns": int(len(r)), "q_values": {}}
        for q in [2, 4, 8, 16]:
            res = vr_lm(r, q)
            if res is not None:
                VR, z_star, p_star, _, _ = res
                kz_out["q_values"][str(q)] = {
                    "vr":             round(VR, 4),
                    "z_star":         round(z_star, 4),
                    "p_value":        round(p_star, 6),
                    "classification": classify(VR, p_star),
                }
        results[kz_name] = kz_out

    return results


# ─────────────────────────────────────────────────────────────────────────────
# PER-INSTRUMENT-TIMEFRAME ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze(symbol: str, tf: str, df: pd.DataFrame, r: np.ndarray, t: np.ndarray) -> dict:
    """Full VR analysis for one instrument-timeframe combo."""
    result = {
        "n_observations": int(len(r)),
        "date_range": {
            "start": str(df["time"].iloc[0]),
            "end":   str(df["time"].iloc[-1]),
        },
        "q_values":              {},
        "chow_denning":          None,
        "overall_classification": "N/A",
        "by_year":               {},
        "temporal_stability":    None,
    }

    # ── Full-sample VR tests ─────────────────────────────────────────────────
    for q in Q_VALUES:
        res = vr_lm(r, q)
        if res is None:
            result["q_values"][str(q)] = None
            continue
        VR, z_star, p_star, z_homo, p_homo = res
        result["q_values"][str(q)] = {
            "vr":             round(VR, 4),
            "z_star":         round(z_star, 4),
            "p_value":        round(p_star, 6),
            "z_homo":         round(z_homo, 4),
            "p_homo":         round(p_homo, 6),
            "classification": classify(VR, p_star),
        }

    # ── Chow-Denning joint test ──────────────────────────────────────────────
    result["chow_denning"] = chow_denning(r, Q_VALUES)

    # ── Overall classification from q=8 (operational timescale proxy) ────────
    q8 = result["q_values"].get("8")
    if q8:
        result["overall_classification"] = q8["classification"]

    # ── Year-by-year breakdown ───────────────────────────────────────────────
    if len(t) > 0:
        try:
            years = pd.DatetimeIndex(t).year
            for yr in sorted(set(years)):
                mask = years == yr
                if mask.sum() < MIN_OBS:
                    continue
                yr_r = r[mask]
                yr_out = {}
                for q in [2, 4, 8, 16]:
                    res = vr_lm(yr_r, q)
                    if res is not None:
                        VR, z_star, p_star, _, _ = res
                        yr_out[str(q)] = {
                            "vr":             round(VR, 4),
                            "z_star":         round(z_star, 4),
                            "p_value":        round(p_star, 6),
                            "classification": classify(VR, p_star),
                            "n_obs":          int(mask.sum()),
                        }
                if yr_out:
                    result["by_year"][str(yr)] = yr_out
        except Exception:
            pass

    # ── Temporal stability ───────────────────────────────────────────────────
    yrs_data = list(result["by_year"].keys())
    if len(yrs_data) >= 2:
        dirs_q8 = []
        for yr in yrs_data:
            q8_yr = result["by_year"][yr].get("8")
            if q8_yr:
                cls = q8_yr["classification"]
                if "MOMENTUM" in cls:
                    dirs_q8.append("MOMENTUM")
                elif "MEAN_REVERSION" in cls:
                    dirs_q8.append("MEAN_REVERSION")
                else:
                    dirs_q8.append("RANDOM_WALK")
        if dirs_q8:
            result["temporal_stability"] = (
                "UNSTABLE" if len(set(dirs_q8)) > 1 else "STABLE"
            )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PLOTTING
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "XAUUSD": "#FFD700",
    "US30":   "#1f77b4",
    "USDJPY": "#2ca02c",
    "GBPJPY": "#d62728",
    "GBPUSD": "#9467bd",
}

def _fmt_cls(cls: str) -> str:
    return (cls
        .replace("MOMENTUM_STRONG",      "MOM↑↑")
        .replace("MOMENTUM_MODERATE",    "MOM↑")
        .replace("MOMENTUM_SUGGESTIVE",  "MOM?")
        .replace("MEAN_REVERSION_STRONG","REV↓↓")
        .replace("MEAN_REVERSION_MODERATE","REV↓")
        .replace("MEAN_REVERSION_SUGGESTIVE","REV?")
        .replace("RANDOM_WALK",          "RW")
        .replace("N/A",                  "N/A"))


def plot_vr_by_q(all_results: dict):
    """One plot per timeframe: VR(q) vs q for all instruments."""
    for tf in ["M15", "H1", "H4", "D1"]:
        fig, ax = plt.subplots(figsize=(10, 6))
        has_data = False
        for sym in INSTRUMENTS:
            tf_data = all_results.get(sym, {}).get(tf)
            if not tf_data:
                continue
            qs, vrs = [], []
            for q in Q_VALUES:
                qd = tf_data["q_values"].get(str(q))
                if qd:
                    qs.append(q); vrs.append(qd["vr"])
            if qs:
                ax.plot(qs, vrs, "o-", color=COLORS[sym], label=sym, lw=2, ms=6)
                has_data = True

        if not has_data:
            plt.close()
            continue

        ax.axhline(1.0, color="black", lw=1.5, ls="--", label="RW (VR=1)")
        for level, ls in [(1.1, ":"), (0.9, ":")]:
            ax.axhline(level, color="gray", lw=0.8, ls=ls, alpha=0.5)
        ax.set_xscale("log", base=2)
        ax.set_xticks(Q_VALUES)
        ax.set_xticklabels([str(q) for q in Q_VALUES])
        ax.set_xlabel("q (holding periods)")
        ax.set_ylabel("Variance Ratio VR(q)")
        ax.set_title(f"VR(q) vs q — {tf} — All Instruments")
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, alpha=0.3)
        fpath = os.path.join(PLOTS_DIR, f"vr_by_q_{tf}.png")
        plt.tight_layout()
        plt.savefig(fpath, dpi=120)
        plt.close()
        print(f"  Saved: {fpath}")


def plot_rolling(all_rolling: dict):
    """Rolling VR(8) time series per instrument-timeframe."""
    for sym in all_rolling:
        for tf in all_rolling[sym]:
            vrs, dates = all_rolling[sym][tf]
            if vrs is None or len(vrs) < 3:
                continue
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(dates, vrs, color=COLORS.get(sym, "blue"), lw=1.8, label="VR(8) 6-month")
            ax.axhline(1.0, color="black", lw=1.5, ls="--", label="Random Walk")
            vr_arr = np.array(vrs)
            ax.fill_between(dates, 1.0, vr_arr, where=vr_arr > 1.0,
                            alpha=0.2, color="green", label="Momentum region")
            ax.fill_between(dates, 1.0, vr_arr, where=vr_arr < 1.0,
                            alpha=0.2, color="red",   label="Mean-reversion region")
            ax.set_xlabel("Date")
            ax.set_ylabel("VR(q=8)")
            ax.set_title(f"Rolling VR(8) — {sym} {tf} — 6-Month Window")
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            fpath = os.path.join(PLOTS_DIR, f"rolling_vr_{sym}_{tf}.png")
            plt.tight_layout()
            plt.savefig(fpath, dpi=100)
            plt.close()
            print(f"  Saved: {fpath}")


# ─────────────────────────────────────────────────────────────────────────────
# MARKDOWN SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def build_summary(all_results: dict) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    L = []

    L += [
        "# Variance Ratio Analysis — GTOS Instruments",
        f"\n**Generated:** {now}",
        "**Method:** Lo-MacKinlay (1988) heteroskedasticity-robust VR test",
        "**Joint test:** Chow-Denning (1993) with Bonferroni correction",
        "",
        "**Classification thresholds (two-sided p-value):**",
        "- p < 0.01 → STRONG",
        "- p < 0.05 → MODERATE  ",
        "- p < 0.10 → SUGGESTIVE (flag, needs more data)",
        "- p ≥ 0.10 → RANDOM WALK",
        "",
        "**Bonferroni correction across full matrix** "
        "(5 instr × 4 TF × 6 q ≈ 120 tests): α_corrected ≈ 0.0004.  ",
        "Only STRONG results (p < 0.01) are robustly significant after correction.",
        "",
        "---",
        "",
        "## Summary Table — Overall classification at VR(q=8)",
        "",
        "| Instrument | M1 | M5 | M15 | H1 | H4 | D1 | H1 stability |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for sym in INSTRUMENTS:
        row = [sym]
        for tf in ["M1", "M5", "M15", "H1", "H4", "D1"]:
            td = all_results.get(sym, {}).get(tf)
            if not td:
                row.append("N/A")
                continue
            row.append(_fmt_cls(td.get("overall_classification", "N/A")))
        # H1 temporal stability
        h1 = all_results.get(sym, {}).get("H1")
        stab = (h1 or {}).get("temporal_stability", "N/A") or "N/A"
        row.append(stab)
        L.append("| " + " | ".join(row) + " |")

    L += [
        "",
        "*MOM=Momentum, REV=Mean-Reversion, RW=Random Walk, "
        "↑↑=p<0.01, ↑=p<0.05, ?=suggestive (p<0.10)*",
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ]

    for sym in INSTRUMENTS:
        L.append(f"### {sym}")
        L.append("")
        for tf in ["M1", "M5", "M15", "H1", "H4", "D1"]:
            td = all_results.get(sym, {}).get(tf)
            if not td:
                continue
            dr = td["date_range"]
            L.append(
                f"#### {sym} {tf} "
                f"({td['n_observations']:,} returns, "
                f"{dr['start'][:10]} – {dr['end'][:10]})"
            )
            L.append("")
            L.append("| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |")
            L.append("|---|---|---|---|---|---|")
            for q in Q_VALUES:
                qd = td["q_values"].get(str(q))
                if qd is None:
                    L.append(f"| {q} | — | — | — | — | insufficient data |")
                    continue
                star = "**" if qd["p_value"] < 0.01 else ("*" if qd["p_value"] < 0.05 else "")
                L.append(
                    f"| {q} | {qd['vr']:.4f} | {qd['z_star']:.3f} | "
                    f"{star}{qd['p_value']:.5f}{star} | "
                    f"{qd['z_homo']:.3f} | {qd['classification']} |"
                )
            cd = td.get("chow_denning")
            if cd:
                L.append(
                    f"\n*Chow-Denning joint test: max|z*| = {cd['max_z_abs']:.3f} "
                    f"(q={cd['q_at_max_z']}), "
                    f"p_Bonferroni = {cd['p_bonferroni']:.4f}*"
                )
            ts = td.get("temporal_stability")
            if ts:
                L.append(f"\n*Temporal stability (H0=stable): **{ts}***")

            # year-by-year table
            by_year = td.get("by_year", {})
            if by_year:
                L.append("\n**Year-by-year at q=8:**\n")
                L.append("| Year | n | VR(8) | z* | p | Classification |")
                L.append("|---|---|---|---|---|---|")
                for yr in sorted(by_year):
                    y8 = by_year[yr].get("8")
                    if y8:
                        star = "**" if y8["p_value"] < 0.01 else ("*" if y8["p_value"] < 0.05 else "")
                        L.append(
                            f"| {yr} | {y8['n_obs']:,} | {y8['vr']:.4f} | "
                            f"{y8['z_star']:.3f} | "
                            f"{star}{y8['p_value']:.5f}{star} | "
                            f"{y8['classification']} |"
                        )
            L.append("")

    # Kill zone section
    kz = (all_results.get("XAUUSD", {}).get("M15") or {}).get("kill_zones")
    if kz:
        L += [
            "---",
            "",
            "## XAUUSD Kill Zone vs All-Hours Analysis (M15)",
            "",
            "| Kill Zone | n returns | q | VR(q) | z* | p-value | Classification |",
            "|---|---|---|---|---|---|---|",
        ]
        for kz_name, kz_data in kz.items():
            if "error" in kz_data:
                L.append(
                    f"| {kz_name} | {kz_data.get('n_bars', kz_data.get('n_returns','?'))} "
                    f"| — | — | — | — | {kz_data['error']} |"
                )
                continue
            for q_str, qd in kz_data.get("q_values", {}).items():
                star = "**" if qd["p_value"] < 0.01 else ("*" if qd["p_value"] < 0.05 else "")
                L.append(
                    f"| {kz_name} | {kz_data['n_returns']} | {q_str} | "
                    f"{qd['vr']:.4f} | {qd['z_star']:.3f} | "
                    f"{star}{qd['p_value']:.5f}{star} | "
                    f"{qd['classification']} |"
                )
        L.append("")

    # GTOS implications
    L += [
        "---",
        "",
        "## GTOS Implications",
        "",
    ]

    # Q1: XAUUSD H1
    L.append("### Q1 — XAUUSD H1 momentum vs mean-reversion?")
    h1x = (all_results.get("XAUUSD") or {}).get("H1")
    if h1x and h1x["q_values"].get("8"):
        qd = h1x["q_values"]["8"]
        L.append(
            f"VR(8) = **{qd['vr']:.4f}**, z* = {qd['z_star']:.3f}, "
            f"p = {qd['p_value']:.5f} → **{qd['classification']}**"
        )
        L.append(
            "(The OB-retest strategy trades on H1 structure; "
            "this classification is the relevant baseline autocorrelation regime.)"
        )
    L.append("")

    # Q2: strongest XAUUSD signal
    L.append("### Q2 — Strongest XAUUSD timescale signal?")
    best = None
    for tf in ["M5", "M15", "H1", "H4", "D1"]:
        td = (all_results.get("XAUUSD") or {}).get(tf)
        if not td:
            continue
        for q_str, qd in (td["q_values"] or {}).items():
            if qd and (best is None or qd["p_value"] < best[3]):
                best = (tf, q_str, qd["classification"], qd["p_value"], qd["vr"])
    if best:
        L.append(
            f"Strongest: **{best[0]} at q={best[1]}**, "
            f"VR={best[4]:.4f}, p={best[3]:.6f} → {best[2]}"
        )
    L.append("")

    # Q3: kill zone
    L.append("### Q3 — Kill zone vs all-hours (XAUUSD M15)?")
    if kz:
        all_q8 = kz.get("All", {}).get("q_values", {}).get("8")
        lon_q8 = kz.get("London", {}).get("q_values", {}).get("8")
        ny_q8  = kz.get("NewYork", {}).get("q_values", {}).get("8")
        if all_q8:
            L.append(f"All-hours  VR(8)={all_q8['vr']:.4f} → {all_q8['classification']}")
        if lon_q8:
            L.append(f"London KZ  VR(8)={lon_q8['vr']:.4f} → {lon_q8['classification']}")
        if ny_q8:
            L.append(f"NY KZ      VR(8)={ny_q8['vr']:.4f} → {ny_q8['classification']}")
        L.append(
            "If KZ classification differs from all-hours, "
            "kill zone selection is capturing a real structural difference."
        )
    L.append("")

    # Q4: temporal stability
    L.append("### Q4 — Temporal stability (edge decay risk)?")
    for sym in INSTRUMENTS:
        h1d = (all_results.get(sym) or {}).get("H1")
        if h1d:
            stab = h1d.get("temporal_stability") or "insufficient years"
            L.append(f"- {sym} H1: {stab}")
    L.append("")

    # Q5: cross-instrument
    L.append("### Q5 — Cross-instrument differences at H1?")
    for sym in INSTRUMENTS:
        h1d = (all_results.get(sym) or {}).get("H1")
        if h1d:
            qd = h1d["q_values"].get("8")
            if qd:
                L.append(
                    f"- {sym} H1: VR(8)={qd['vr']:.4f} "
                    f"p={qd['p_value']:.5f} → {qd['classification']}"
                )
    L.append("")

    L += [
        "---",
        "",
        "## Statistical Caveats",
        "",
        "- Bonferroni threshold for 120 simultaneous tests: α/120 ≈ 0.0004.  ",
        "  Only **STRONG** results (p < 0.01) are robustly significant after correction.",
        "- D1 data: n < 2000, q=64 gives T/q < 30 — treat D1 q=64 as exploratory.",
        "- XAUUSD M1: only ~4 months of data — results are exploratory only.",
        "- Weekend/overnight gap returns are excluded from intraday VR (gaps > 3× expected bar).",
        "- Kill zone VR: consecutive within-session returns concatenated across all dates;",
        "  captures within-kill-zone autocorrelation structure, not cross-session momentum.",
        "- Rolling VR(8) uses a 6-month window rolled monthly; short windows amplify noise.",
    ]

    return "\n".join(L)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("GTOS Variance Ratio Analysis")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Data:    {DATA_DIR}")
    print(f"Output:  {OUTPUT_DIR}")
    print("=" * 64)

    all_results  = {}
    all_rolling  = {}

    for sym, cfg in INSTRUMENTS.items():
        print(f"\n{'-'*40}")
        print(f"  {sym}")
        all_results[sym] = {}
        all_rolling[sym] = {}

        for tf in cfg["tfs"]:
            df = load_csv(sym, tf)
            if df is None:
                print(f"    {tf}: no file")
                continue

            r, t = compute_log_returns(df, tf)
            print(
                f"    {tf}: {len(df):,} bars -> {len(r):,} returns  "
                f"[{df['time'].iloc[0].strftime('%Y-%m-%d')} to "
                f"{df['time'].iloc[-1].strftime('%Y-%m-%d')}]"
            )

            if len(r) < MIN_OBS:
                print(f"         ↳ skip: n < {MIN_OBS}")
                continue

            result = analyze(sym, tf, df, r, t)
            all_results[sym][tf] = result

            # XAUUSD M15 kill zone
            if sym == "XAUUSD" and tf == "M15":
                result["kill_zones"] = kill_zone_vr(df)

            # Rolling VR for H1 and H4
            if tf in ("H1", "H4", "M15"):
                vrs, dates = rolling_vr(r, t, q=8, tf=tf)
                if vrs is not None:
                    all_rolling[sym][tf] = (vrs, dates)
                    print(f"         rolling VR(8): {len(vrs)} windows"  .encode('ascii','replace').decode())

            # Quick summary line
            for q in [4, 8, 16]:
                qd = result["q_values"].get(str(q))
                if qd:
                    print(
                        f"         VR({q:2d})={qd['vr']:.4f}  "
                        f"z*={qd['z_star']:+.2f}  "
                        f"p={qd['p_value']:.4f}  "
                        f"-> {qd['classification']}"
                    )

    # ── Version output files ─────────────────────────────────────────────────
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    json_path = os.path.join(OUTPUT_DIR, f"variance_ratio_results_{ts}.json")
    with open(json_path, "w") as fh:
        json.dump(all_results, fh, indent=2, default=str)
    print(f"\nJSON saved:  {json_path}")

    md_path = os.path.join(OUTPUT_DIR, f"variance_ratio_summary_{ts}.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(build_summary(all_results))
    print(f"MD saved:    {md_path}")

    print("\nGenerating plots …")
    plot_vr_by_q(all_results)
    plot_rolling(all_rolling)

    print(f"\nDone.  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    return json_path, md_path


if __name__ == "__main__":
    main()
