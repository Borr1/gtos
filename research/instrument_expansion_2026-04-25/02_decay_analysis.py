"""Per-instrument decay deep-dive — Tier 1 Agent #2 (instrument expansion 2026-04-25).

Computes monthly metrics across 24 instruments for Jan / Feb / Mar / Apr 2026
and identifies STABLE / DECAYING / IMPROVING / VOLATILE labels per metric.

Pure Python + numpy/pandas/scipy. $0 API. No CEO-approved-config touched.

Outputs (under research/instrument_expansion_2026-04-25/):
- 02_DECAY_ANALYSIS.md          (narrative + tables)
- 02_per_instrument_decay_scorecard.csv
- 02_monthly_metrics.csv        (long format)
- 02_h1_h2_split.csv
- 02_decay_clusters.csv

Methodology mirrors phase1_full_extraction (XAUUSD WR decay) and
research/touch_count_audit/REVIEWER_PASS.md (H1/H2 split).
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

# Ensure src/ importable
try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:
    ROOT = Path(os.getcwd()).resolve()
sys.path.insert(0, str(ROOT))

# Re-use production swing/structure detector for cross-instrument consistency
from src.components.market_state import (  # noqa: E402
    avg_candle_body,
    calculate_atr,
    detect_structure_breaks,
    detect_swings,
    identify_fvgs,
    identify_order_blocks,
    identify_structure_v2,
)
from src.models.market_state_models import EqualLevel  # noqa: E402

DATA_DIR = ROOT / "data" / "historical_2026"
OUT_DIR = ROOT / "research" / "instrument_expansion_2026-04-25"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INSTRUMENTS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD",
    "EURGBP", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD",
    "GER40", "JP225", "NAS100", "NZDUSD", "SPX500",
    "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
    "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
]

# H1 BOS retest evaluation horizon (in H1 bars)
H1_RETEST_HORIZON = 12
# Equal-H/L sweep+reversal evaluation horizon (in M15 bars)
SWEEP_HORIZON_M15 = 16
# Equal-level tolerance (multiple of bar's ATR)
EQUAL_TOL_ATR_MULT = 0.10
# Sweep reversal threshold (multiple of M15 ATR)
SWEEP_REVERSAL_THRESH_ATR = 0.5

MONTH_LABELS = {"2026-01": "Jan", "2026-02": "Feb", "2026-03": "Mar", "2026-04": "Apr"}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _to_candle_dicts(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame slice to the candle-dict format market_state uses."""
    return [
        {
            "time": str(t),
            "open": float(o),
            "high": float(h),
            "low": float(l),
            "close": float(c),
            "volume": int(v) if not pd.isna(v) else 0,
        }
        for t, o, h, l, c, v in zip(df["time"].astype(str), df["open"], df["high"], df["low"], df["close"], df["volume"])
    ]


def _load(symbol: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    m15 = pd.read_csv(DATA_DIR / f"{symbol}_M15.csv", parse_dates=["time"])
    h1 = pd.read_csv(DATA_DIR / f"{symbol}_H1.csv", parse_dates=["time"])
    m15["month"] = m15["time"].dt.strftime("%Y-%m")
    h1["month"] = h1["time"].dt.strftime("%Y-%m")
    return m15, h1


def _atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder ATR(period) over a candle DataFrame; returns same index as df."""
    h_l = df["high"] - df["low"]
    h_pc = (df["high"] - df["close"].shift(1)).abs()
    l_pc = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    # Wilder smoothing (recursive EWM with alpha = 1/period after seed)
    atr = tr.copy()
    seed = tr.iloc[1 : period + 1].mean()
    atr.iloc[:period] = np.nan
    if not np.isnan(seed):
        atr.iloc[period] = seed
        for i in range(period + 1, len(atr)):
            atr.iloc[i] = (atr.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period
    return atr


def _displacement_rate_monthly(m15_df: pd.DataFrame) -> dict[str, float]:
    """Per-month displacement rate = body / avg-body-20 >= 1.5."""
    bodies = (m15_df["close"] - m15_df["open"]).abs()
    avg_body_20 = bodies.rolling(20, min_periods=20).mean()
    disp = (bodies / avg_body_20.replace(0, np.nan)) >= 1.5
    out = {}
    for mo, g in m15_df.assign(disp=disp).groupby("month"):
        n = g["disp"].notna().sum()
        if n == 0:
            continue
        out[mo] = float(g["disp"].sum()) / float(n)
    return out


def _equal_levels(df: pd.DataFrame, side: str, atr_series: pd.Series, tol_mult: float = EQUAL_TOL_ATR_MULT,
                  window: int = 50) -> list[tuple[int, float, int]]:
    """Detect equal-H or equal-L formation. Returns list of (formation_idx, level, partner_idx).

    A pair (i, j) is "equal" if abs(price_i - price_j) <= tol_mult * atr_at_j and i + 5 <= j <= i + window.
    Only first-pair occurrences are kept.
    """
    pairs = []
    used = set()
    prices = df["high"].to_numpy() if side == "high" else df["low"].to_numpy()
    n = len(prices)
    for j in range(5, n):
        atr_j = atr_series.iloc[j]
        if not np.isfinite(atr_j) or atr_j <= 0:
            continue
        tol = tol_mult * atr_j
        i_min = max(0, j - window)
        for i in range(i_min, j - 4):
            if i in used or j in used:
                continue
            if abs(prices[i] - prices[j]) <= tol:
                pairs.append((i, float(prices[i]), j))
                used.add(i)
                used.add(j)
                break
    return pairs


def _hurst(ts: np.ndarray, max_lag: int = 50) -> float:
    """Hurst exponent via R/S analysis. >0.5 = trending, <0.5 = mean-reverting."""
    ts = ts[np.isfinite(ts)]
    if len(ts) < max_lag * 2:
        return float("nan")
    lags = list(range(2, max_lag))
    tau = []
    for lag in lags:
        diffs = ts[lag:] - ts[:-lag]
        if len(diffs) < 2:
            continue
        s = np.std(diffs)
        if s <= 0:
            continue
        tau.append(s)
    if len(tau) < 5:
        return float("nan")
    log_lags = np.log(lags[: len(tau)])
    log_tau = np.log(tau)
    slope, _, _, _, _ = stats.linregress(log_lags, log_tau)
    return float(slope)


def _autocorr(x: np.ndarray, lag: int) -> float:
    x = x[np.isfinite(x)]
    if len(x) <= lag + 1:
        return float("nan")
    a = x[: -lag]
    b = x[lag:]
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _compute_h1_bos_retest_wr(h1_df: pd.DataFrame) -> dict[str, dict]:
    """Per H1-month: count H1 BOS events, evaluate retest within H1_RETEST_HORIZON bars.

    Methodology:
    - Detect swings on the FULL H1 series.
    - identify_structure_v2 on rolling 168-bar windows ending at each H1 bar.
    - On each window, run detect_structure_breaks → if newest event is a BOS,
      identify the OB at that BOS and evaluate retest:
        * Continuation = price re-enters OB then moves +1.5 * ATR_H1 in BOS
          direction within H1_RETEST_HORIZON bars BEFORE moving -1.0 ATR against.
    - Implied WR per month = continuations / BOS_count.

    Note: This is a *mechanical* proxy — no AI filter. It captures whether the
    raw OB-retest mechanism still has edge per instrument.
    """
    candles_all = _to_candle_dicts(h1_df)
    swings_all = detect_swings(candles_all, min_bars=2)
    atr_h1 = _atr_series(h1_df, period=14)

    bos_per_month: dict[str, list[dict]] = {}
    win_size = 168
    step = 4  # slide window every 4 bars (instead of every bar — 4× faster, same coverage)

    # Capture every BOS event seen in any window, dedup by (global_break_idx, direction).
    # Each BOS gets the OB causing it (10-bar lookback per market_state.identify_order_blocks).
    seen_bos_global: dict[tuple[int, str], dict] = {}

    for end_idx in range(win_size, len(candles_all), step):
        win_candles = candles_all[end_idx - win_size: end_idx]
        win_swings = [s for s in swings_all if end_idx - win_size <= s.index < end_idx]
        local_swings = []
        for s in win_swings:
            local_swings.append(type(s)(
                index=s.index - (end_idx - win_size),
                type=s.type,
                price=s.price,
                time=s.time,
            ))
        if len(local_swings) < 4:
            continue
        struct = identify_structure_v2(local_swings)
        if struct.direction not in ("bullish", "bearish"):
            continue
        events = detect_structure_breaks(win_candles, local_swings, struct)
        for ev in events:
            if ev.type != "BOS":
                continue
            global_break_idx = (end_idx - win_size) + ev.candle_index
            key = (global_break_idx, ev.direction)
            if key in seen_bos_global:
                continue
            obs = identify_order_blocks(win_candles, [ev])
            if not obs:
                continue
            ob = obs[0]
            atr_at_break = atr_h1.iloc[global_break_idx] if global_break_idx < len(atr_h1) else np.nan
            if not np.isfinite(atr_at_break) or atr_at_break <= 0:
                continue
            mo = h1_df.iloc[global_break_idx]["month"]
            seen_bos_global[key] = {
                "break_idx": int(global_break_idx),
                "direction": ev.direction,
                "ob_high": float(ob.high),
                "ob_low": float(ob.low),
                "atr": float(atr_at_break),
                "month": mo,
            }
    # Index by month
    for d in seen_bos_global.values():
        bos_per_month.setdefault(d["month"], []).append(d)

    # Now evaluate retests. Per BOS: scan from break_idx+1 forward
    #   - Find first bar where price re-enters [ob_low, ob_high].
    #   - From that retest bar, scan up to H1_RETEST_HORIZON bars:
    #     bullish: TP = retest_low + 1.5 * atr; SL = retest_low - 1.0 * atr
    #     bearish: TP = retest_high - 1.5 * atr; SL = retest_high + 1.0 * atr
    #   - First touched determines outcome.
    out: dict[str, dict] = {}
    highs_arr = h1_df["high"].to_numpy()
    lows_arr = h1_df["low"].to_numpy()

    for mo, bos_list in bos_per_month.items():
        wins = 0
        evals = 0
        for b in bos_list:
            i0 = b["break_idx"]
            # Look ahead 30 bars for retest
            retest_idx = None
            for k in range(i0 + 1, min(i0 + 30, len(h1_df))):
                if lows_arr[k] <= b["ob_high"] and highs_arr[k] >= b["ob_low"]:
                    retest_idx = k
                    break
            if retest_idx is None:
                continue
            atr = b["atr"]
            if b["direction"] == "bullish":
                entry = b["ob_high"]
                tp = entry + 1.5 * atr
                sl = b["ob_low"] - 1.0 * atr
            else:
                entry = b["ob_low"]
                tp = entry - 1.5 * atr
                sl = b["ob_high"] + 1.0 * atr

            # Scan forward up to H1_RETEST_HORIZON bars
            outcome = None
            for k in range(retest_idx, min(retest_idx + H1_RETEST_HORIZON, len(h1_df))):
                hi = highs_arr[k]
                lo = lows_arr[k]
                if b["direction"] == "bullish":
                    if lo <= sl:
                        outcome = "loss"
                        break
                    if hi >= tp:
                        outcome = "win"
                        break
                else:
                    if hi >= sl:
                        outcome = "loss"
                        break
                    if lo <= tp:
                        outcome = "win"
                        break
            if outcome is None:
                continue
            evals += 1
            if outcome == "win":
                wins += 1
        if evals > 0:
            out[mo] = {"wr": wins / evals, "n": evals}
    return out


def _compute_sweep_reversal_wr(m15_df: pd.DataFrame) -> dict[str, dict]:
    """Sweep+reversal proxy WR per month.

    For each detected equal-high pair (i, j): on bar j+k (k <= SWEEP_HORIZON_M15),
    if a wick exceeds the equal-high level by > 0 then the body must close back
    BELOW the level by >= SWEEP_REVERSAL_THRESH_ATR * ATR_M15(j) within
    SWEEP_HORIZON_M15 bars. Symmetric for equal-lows (sweeping low → reversal up).
    """
    atr_m15 = _atr_series(m15_df, period=14)
    out: dict[str, dict] = {}

    eh_pairs = _equal_levels(m15_df, "high", atr_m15)
    el_pairs = _equal_levels(m15_df, "low", atr_m15)

    highs = m15_df["high"].to_numpy()
    lows = m15_df["low"].to_numpy()
    closes = m15_df["close"].to_numpy()

    # Equal-highs → expect downside reversal
    events_per_month: dict[str, list[bool]] = {}
    for (i, level, j) in eh_pairs:
        if j + 1 >= len(m15_df):
            continue
        atr_j = atr_m15.iloc[j]
        if not np.isfinite(atr_j) or atr_j <= 0:
            continue
        threshold = level - SWEEP_REVERSAL_THRESH_ATR * atr_j
        # Find first sweep bar after j
        sweep_idx = None
        for k in range(j + 1, min(j + SWEEP_HORIZON_M15, len(m15_df))):
            if highs[k] > level:
                sweep_idx = k
                break
        if sweep_idx is None:
            continue
        # Check for reversal close within remaining horizon
        success = False
        for k in range(sweep_idx, min(sweep_idx + SWEEP_HORIZON_M15, len(m15_df))):
            if closes[k] <= threshold:
                success = True
                break
        mo = m15_df.iloc[j]["month"]
        events_per_month.setdefault(mo, []).append(success)

    for (i, level, j) in el_pairs:
        if j + 1 >= len(m15_df):
            continue
        atr_j = atr_m15.iloc[j]
        if not np.isfinite(atr_j) or atr_j <= 0:
            continue
        threshold = level + SWEEP_REVERSAL_THRESH_ATR * atr_j
        sweep_idx = None
        for k in range(j + 1, min(j + SWEEP_HORIZON_M15, len(m15_df))):
            if lows[k] < level:
                sweep_idx = k
                break
        if sweep_idx is None:
            continue
        success = False
        for k in range(sweep_idx, min(sweep_idx + SWEEP_HORIZON_M15, len(m15_df))):
            if closes[k] >= threshold:
                success = True
                break
        mo = m15_df.iloc[j]["month"]
        events_per_month.setdefault(mo, []).append(success)

    for mo, vs in events_per_month.items():
        if not vs:
            continue
        out[mo] = {"wr": sum(vs) / len(vs), "n": len(vs)}
    return out


def _compute_structural_rates(h1_df: pd.DataFrame, m15_df: pd.DataFrame) -> dict[str, dict]:
    """Per-month rates: BOS/day, CHoCH/day, OB formation, FVG density.

    Operates on rolling 168-bar H1 windows for BOS/CHoCH/OB and on full-month
    M15 slices for FVG.
    """
    candles_all = _to_candle_dicts(h1_df)
    swings_all = detect_swings(candles_all, min_bars=2)
    win_size = 168

    bos_per_month: dict[str, set] = {}
    choch_per_month: dict[str, set] = {}
    ob_per_month: dict[str, set] = {}
    days_per_month: dict[str, set] = {}

    for idx, row in h1_df.iterrows():
        days_per_month.setdefault(row["month"], set()).add(row["time"].date())

    for end_idx in range(win_size, len(candles_all)):
        win_candles = candles_all[end_idx - win_size: end_idx]
        win_swings = [s for s in swings_all if end_idx - win_size <= s.index < end_idx]
        local_swings = []
        for s in win_swings:
            local_swings.append(type(s)(
                index=s.index - (end_idx - win_size),
                type=s.type,
                price=s.price,
                time=s.time,
            ))
        if len(local_swings) < 4:
            continue
        struct = identify_structure_v2(local_swings)
        if struct.direction in ("insufficient_data", "transitional"):
            continue
        events = detect_structure_breaks(win_candles, local_swings, struct)
        for e in events:
            global_idx = (end_idx - win_size) + e.candle_index
            mo = h1_df.iloc[global_idx]["month"]
            key = (global_idx, e.type, e.direction)
            if e.type == "BOS":
                bos_per_month.setdefault(mo, set()).add(key)
            elif e.type == "CHoCH":
                choch_per_month.setdefault(mo, set()).add(key)
        obs = identify_order_blocks(win_candles, events)
        for ob in obs:
            global_idx = (end_idx - win_size) + ob.formation_index
            mo = h1_df.iloc[global_idx]["month"]
            ob_per_month.setdefault(mo, set()).add((global_idx, ob.type))

    out: dict[str, dict] = {}
    months = sorted(set(list(bos_per_month.keys()) + list(choch_per_month.keys()) + list(days_per_month.keys())))
    for mo in months:
        ndays = max(1, len(days_per_month.get(mo, set())))
        out[mo] = {
            "bos_count": len(bos_per_month.get(mo, set())),
            "choch_count": len(choch_per_month.get(mo, set())),
            "ob_count": len(ob_per_month.get(mo, set())),
            "trading_days": ndays,
            "bos_per_day": len(bos_per_month.get(mo, set())) / ndays,
            "choch_per_day": len(choch_per_month.get(mo, set())) / ndays,
            "ob_per_day": len(ob_per_month.get(mo, set())) / ndays,
        }

    # FVG density per 100 M15 candles (per month)
    for mo, g in m15_df.groupby("month"):
        candles = _to_candle_dicts(g)
        if not candles:
            continue
        atr_m15_full = _atr_series(g, period=14)
        # Use median ATR as min-gap-size (matches market_state default heuristic)
        med_atr = float(atr_m15_full.median()) if atr_m15_full.notna().any() else 0.0
        min_gap = med_atr * 0.10
        fvgs = identify_fvgs(candles, min_gap_size=min_gap)
        out.setdefault(mo, {})
        out[mo]["m15_candles"] = len(candles)
        out[mo]["fvg_count"] = len(fvgs)
        out[mo]["fvg_per_100"] = len(fvgs) / len(candles) * 100.0

    return out


def _equal_level_count_per_month(m15_df: pd.DataFrame) -> dict[str, int]:
    atr_m15 = _atr_series(m15_df, period=14)
    eh_pairs = _equal_levels(m15_df, "high", atr_m15)
    el_pairs = _equal_levels(m15_df, "low", atr_m15)
    out: dict[str, int] = {}
    for _, _, j in eh_pairs + el_pairs:
        mo = m15_df.iloc[j]["month"]
        out[mo] = out.get(mo, 0) + 1
    return out


# -----------------------------------------------------------------------------
# Stats helpers
# -----------------------------------------------------------------------------
def _wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _two_sample_t(a: list[float], b: list[float]) -> tuple[float, float]:
    """Welch's t-test on two samples. Returns (t_stat, p_value)."""
    if len(a) < 2 or len(b) < 2:
        return (float("nan"), float("nan"))
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return (float(t), float(p))


def _trend(values: list[float], months: list[float]) -> tuple[float, float, float]:
    """Linear regression slope, p-value, R². months should be 1, 2, 3, 4."""
    if len(values) < 3:
        return (float("nan"), float("nan"), float("nan"))
    slope, _, r, p, _ = stats.linregress(months, values)
    return (float(slope), float(p), float(r * r))


def _stability_score(monthly: list[float]) -> float:
    """1 / (1 + std/|mean|)."""
    if not monthly or len(monthly) < 2:
        return float("nan")
    mu = np.mean(monthly)
    sd = np.std(monthly)
    if abs(mu) < 1e-12:
        return float("nan")
    return float(1.0 / (1.0 + sd / abs(mu)))


def _direction_label(slope: float, p: float, monthly: list[float], stability: float, lower_better: bool = False) -> str:
    """STABLE / DECAYING / IMPROVING / VOLATILE.

    "Decaying" = slope significantly negative for higher-better metrics
    OR significantly positive for lower-better metrics, AND stability < 0.7.
    """
    if not np.isfinite(slope):
        return "NA"
    sig = np.isfinite(p) and p < 0.10  # Lenient given n=4 months
    if sig:
        if (slope < 0 and not lower_better) or (slope > 0 and lower_better):
            return "DECAYING"
        return "IMPROVING"
    if np.isfinite(stability) and stability >= 0.85:
        return "STABLE"
    return "VOLATILE"


# -----------------------------------------------------------------------------
# Main per-instrument analysis
# -----------------------------------------------------------------------------
@dataclass
class InstrumentResult:
    symbol: str
    monthly: dict  # month -> {metric: value}
    h1h2: dict  # metric -> {h1_mean, h2_mean, p, delta}
    trends: dict  # metric -> {slope, p, r2, direction}
    stability: dict  # metric -> stability score
    decay_score: float
    composite_dir: str


def analyze_instrument(symbol: str) -> InstrumentResult:
    print(f"  -> {symbol} ", end="", flush=True)
    m15, h1 = _load(symbol)

    # Volatility
    atr_m15 = _atr_series(m15, period=14)
    atr_h1 = _atr_series(h1, period=14)
    sq_ret_m15 = (m15["close"].pct_change()) ** 2

    monthly = {}
    months = sorted(m15["month"].unique())
    for mo in months:
        mask_m15 = m15["month"] == mo
        mask_h1 = h1["month"] == mo
        m15_slice = m15[mask_m15]
        h1_slice = h1[mask_h1]
        if len(m15_slice) < 200 or len(h1_slice) < 50:
            continue
        # Flag low-confidence months (typical month has ~2000 M15 candles)
        # Apr-only partial data with <800 candles ≈ <8 trading days
        low_conf = (mo == "2026-04" and len(m15_slice) < 800) or len(m15_slice) < 800
        # Vol
        atr_m15_mean = float(atr_m15[mask_m15].mean())
        atr_h1_mean = float(atr_h1[mask_h1].mean())
        # Vol persistence: lag-1 autocorr of squared returns
        vol_persist = _autocorr(sq_ret_m15[mask_m15].to_numpy(), lag=1)
        # Trend persistence
        log_ret = np.log(m15_slice["close"] / m15_slice["close"].shift(1)).to_numpy()
        ac1 = _autocorr(log_ret, lag=1)
        ac5 = _autocorr(log_ret, lag=5)
        # Hurst
        hurst = _hurst(np.cumsum(np.where(np.isfinite(log_ret), log_ret, 0)))
        # Displacement rate (M15)
        bodies = (m15_slice["close"] - m15_slice["open"]).abs()
        avg_b = avg_candle_body(_to_candle_dicts(m15_slice), period=20)
        if avg_b > 0:
            disp_rate = float((bodies >= 1.5 * avg_b).mean())
        else:
            disp_rate = float("nan")

        monthly[mo] = {
            "atr_m15": atr_m15_mean,
            "atr_h1": atr_h1_mean,
            "vol_persistence": vol_persist,
            "ac1_logret": ac1,
            "ac5_logret": ac5,
            "hurst": hurst,
            "displacement_rate": disp_rate,
            "m15_candle_count": len(m15_slice),
            "h1_candle_count": len(h1_slice),
            "low_confidence": int(low_conf),
        }

    # Structural rates
    struct_rates = _compute_structural_rates(h1, m15)
    eq_counts = _equal_level_count_per_month(m15)
    for mo, d in struct_rates.items():
        if mo not in monthly:
            continue
        for k, v in d.items():
            monthly[mo][k] = v
        monthly[mo]["equal_levels"] = eq_counts.get(mo, 0)

    # Mechanical edge proxies
    h1_wr = _compute_h1_bos_retest_wr(h1)
    sweep_wr = _compute_sweep_reversal_wr(m15)
    for mo in monthly:
        monthly[mo]["h1_bos_retest_wr"] = h1_wr.get(mo, {}).get("wr", float("nan"))
        monthly[mo]["h1_bos_retest_n"] = h1_wr.get(mo, {}).get("n", 0)
        monthly[mo]["sweep_reversal_wr"] = sweep_wr.get(mo, {}).get("wr", float("nan"))
        monthly[mo]["sweep_reversal_n"] = sweep_wr.get(mo, {}).get("n", 0)

    # Sort months and prep H1/H2 split
    sorted_months = sorted(monthly.keys())
    h1_months = [m for m in sorted_months if m in {"2026-01", "2026-02"}]
    h2_months = [m for m in sorted_months if m in {"2026-03", "2026-04"}]

    metrics = ["atr_m15", "atr_h1", "vol_persistence", "ac1_logret", "ac5_logret",
               "hurst", "displacement_rate", "bos_per_day", "choch_per_day",
               "ob_per_day", "fvg_per_100", "equal_levels",
               "h1_bos_retest_wr", "sweep_reversal_wr"]

    h1h2 = {}
    trends = {}
    stability = {}

    # For WR metrics, we want pooled samples for the t-test (binomial)
    # For all others, the per-month means are scalar; t-test on n=2 vs n=2 is barely
    # informative — we report mean delta as the primary signal and Wilson CIs for WRs.
    for met in metrics:
        h1_vals = [monthly[mo][met] for mo in h1_months
                   if met in monthly[mo] and isinstance(monthly[mo][met], (int, float)) and np.isfinite(monthly[mo][met])]
        h2_vals = [monthly[mo][met] for mo in h2_months
                   if met in monthly[mo] and isinstance(monthly[mo][met], (int, float)) and np.isfinite(monthly[mo][met])]
        if len(h1_vals) >= 1 and len(h2_vals) >= 1:
            h1_mean = float(np.mean(h1_vals))
            h2_mean = float(np.mean(h2_vals))
            delta = h2_mean - h1_mean
        else:
            h1_mean = float("nan"); h2_mean = float("nan"); delta = float("nan")

        if met in ("h1_bos_retest_wr", "sweep_reversal_wr"):
            # Pooled binomial proportions test
            n_field = "h1_bos_retest_n" if met == "h1_bos_retest_wr" else "sweep_reversal_n"
            h1_wins = sum(int(round(monthly[mo][met] * monthly[mo][n_field]))
                          for mo in h1_months if np.isfinite(monthly[mo].get(met, float("nan"))))
            h1_n = sum(monthly[mo][n_field] for mo in h1_months if monthly[mo][n_field] > 0)
            h2_wins = sum(int(round(monthly[mo][met] * monthly[mo][n_field]))
                          for mo in h2_months if np.isfinite(monthly[mo].get(met, float("nan"))))
            h2_n = sum(monthly[mo][n_field] for mo in h2_months if monthly[mo][n_field] > 0)
            if h1_n >= 5 and h2_n >= 5:
                # Two-proportion z-test
                p_h1 = h1_wins / h1_n
                p_h2 = h2_wins / h2_n
                p_pool = (h1_wins + h2_wins) / (h1_n + h2_n)
                se = math.sqrt(p_pool * (1 - p_pool) * (1/h1_n + 1/h2_n))
                if se > 0:
                    z = (p_h1 - p_h2) / se
                    p_val = 2 * (1 - stats.norm.cdf(abs(z)))
                else:
                    p_val = float("nan")
                h1h2[met] = {
                    "h1_mean": p_h1, "h2_mean": p_h2, "delta": p_h2 - p_h1,
                    "p_value": float(p_val), "h1_n": h1_n, "h2_n": h2_n,
                }
            else:
                h1h2[met] = {
                    "h1_mean": h1_mean, "h2_mean": h2_mean, "delta": delta,
                    "p_value": float("nan"), "h1_n": h1_n, "h2_n": h2_n,
                }
        else:
            t, p = _two_sample_t(h1_vals, h2_vals) if (len(h1_vals) >= 2 and len(h2_vals) >= 2) else (float("nan"), float("nan"))
            h1h2[met] = {
                "h1_mean": h1_mean, "h2_mean": h2_mean, "delta": delta,
                "p_value": p, "h1_n": len(h1_vals), "h2_n": len(h2_vals),
            }

        # Trend regression
        m_idx = []
        m_vals = []
        for i, mo in enumerate(sorted_months):
            v = monthly[mo].get(met, float("nan"))
            if isinstance(v, (int, float)) and np.isfinite(v):
                m_idx.append(i + 1)
                m_vals.append(v)
        slope, p_trend, r2 = _trend(m_vals, m_idx)
        stab = _stability_score(m_vals)
        # higher-is-better defaults; volatility (atr) and choch_per_day/equal_levels
        # don't have a monotonic interpretation — flag as volatility metrics, no decay direction
        lower_better = met in ("vol_persistence",)  # higher persistence = clustered → can be neutral
        # We treat "decay" only on edge metrics
        if met in ("h1_bos_retest_wr", "sweep_reversal_wr", "bos_per_day", "ob_per_day", "fvg_per_100", "displacement_rate"):
            direction = _direction_label(slope, p_trend, m_vals, stab, lower_better=False)
        else:
            direction = _direction_label(slope, p_trend, m_vals, stab, lower_better=False)
        trends[met] = {"slope": slope, "p_value": p_trend, "r2": r2, "direction": direction}
        stability[met] = stab

    # ---- Composite decay score (0-100) ----
    # Anchor on the strongest empirical signals:
    #   1. H1→H2 H1-BOS-retest-WR delta + Cochran-Armitage trend p-value
    #   2. H1→H2 sweep-reversal-WR delta + p-value
    #   3. ob_per_day H1→H2 % change (structural supply)
    #   4. displacement_rate H1→H2 % change
    #
    # Score interpretation:
    #   <30  STABLE     - no decay signal
    #   30-50 NEUTRAL   - mixed
    #   50-70 ELEVATED  - directional decay, not yet significant
    #   >70  HIGH RISK  - decay confirmed in multiple metrics
    score = 0.0
    score_components: dict[str, float] = {}

    # H1 BOS retest WR (PRIMARY mechanism — ob_retest framework)
    bos_h = h1h2.get("h1_bos_retest_wr", {})
    bos_delta = bos_h.get("delta", 0.0) or 0.0
    bos_p = bos_h.get("p_value")
    bos_n_total = (bos_h.get("h1_n", 0) or 0) + (bos_h.get("h2_n", 0) or 0)
    if np.isfinite(bos_delta) and bos_n_total >= 30:
        # 25 points if delta < -0.10 (≥10pp WR drop), scaled
        comp_bos = max(-30.0, min(30.0, -bos_delta * 100.0))
        # Boost if p-value is significant
        if bos_p is not None and np.isfinite(bos_p) and bos_p < 0.10 and bos_delta < 0:
            comp_bos += 10.0
        score_components["h1_bos_wr"] = comp_bos
        score += comp_bos

    # Sweep reversal WR (secondary mechanism — relevant for sweep+reversal framework)
    sw_h = h1h2.get("sweep_reversal_wr", {})
    sw_delta = sw_h.get("delta", 0.0) or 0.0
    sw_p = sw_h.get("p_value")
    sw_n_total = (sw_h.get("h1_n", 0) or 0) + (sw_h.get("h2_n", 0) or 0)
    if np.isfinite(sw_delta) and sw_n_total >= 100:
        comp_sw = max(-15.0, min(15.0, -sw_delta * 75.0))
        if sw_p is not None and np.isfinite(sw_p) and sw_p < 0.05 and sw_delta < 0:
            comp_sw += 5.0
        score_components["sweep_wr"] = comp_sw
        score += comp_sw

    # OB supply change (proxy: H1→H2 % change in ob_per_day)
    ob_h = h1h2.get("ob_per_day", {})
    if np.isfinite(ob_h.get("h1_mean", float("nan"))) and ob_h["h1_mean"] > 0:
        ob_pct = (ob_h["h2_mean"] - ob_h["h1_mean"]) / ob_h["h1_mean"]
        comp_ob = max(-15.0, min(15.0, -ob_pct * 75.0))
        score_components["ob_per_day"] = comp_ob
        score += comp_ob

    # Displacement rate (impulse-quality proxy)
    disp_h = h1h2.get("displacement_rate", {})
    if np.isfinite(disp_h.get("h1_mean", float("nan"))) and disp_h["h1_mean"] > 0:
        disp_pct = (disp_h["h2_mean"] - disp_h["h1_mean"]) / disp_h["h1_mean"]
        comp_disp = max(-10.0, min(10.0, -disp_pct * 30.0))
        score_components["displacement"] = comp_disp
        score += comp_disp

    # Volatility regime change (informational, not punitive)
    atr_h = h1h2.get("atr_m15", {})
    if np.isfinite(atr_h.get("h1_mean", float("nan"))) and atr_h["h1_mean"] > 0:
        atr_pct = abs(atr_h["h2_mean"] - atr_h["h1_mean"]) / atr_h["h1_mean"]
        # Penalize ONLY if vol fell sharply (less opportunity)
        if atr_h["h2_mean"] < atr_h["h1_mean"] * 0.85:
            score_components["vol_regime"] = 5.0
            score += 5.0

    # Translate raw score (centered ~0) to 0-100 range
    # raw range roughly -75 to +75 → mapped to 25..75 typical, with 50 center
    decay_score = max(0.0, min(100.0, 50.0 + score))

    # Composite direction
    edge_metrics = ["h1_bos_retest_wr", "ob_per_day", "displacement_rate"]
    if decay_score >= 65:
        composite_dir = "DECAYING"
    elif decay_score <= 35:
        composite_dir = "IMPROVING" if (bos_delta > 0.05 or sw_delta > 0.02) else "STABLE"
    else:
        # Tie-break on H1→H2 BOS WR alone
        if bos_delta < -0.05 and bos_n_total >= 30:
            composite_dir = "MILD_DECAY"
        elif abs(bos_delta) < 0.03 and bos_n_total >= 30:
            composite_dir = "STABLE"
        else:
            composite_dir = "VOLATILE"

    print(f"[months={len(monthly)} score={decay_score:.0f} {composite_dir}]")

    return InstrumentResult(
        symbol=symbol,
        monthly=monthly,
        h1h2=h1h2,
        trends=trends,
        stability=stability,
        decay_score=decay_score,
        composite_dir=composite_dir,
    )


def main():
    print(f"Output dir: {OUT_DIR}")
    print(f"Analyzing {len(INSTRUMENTS)} instruments...")

    results: list[InstrumentResult] = []
    for sym in INSTRUMENTS:
        try:
            r = analyze_instrument(sym)
            results.append(r)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {sym}: {e}")

    # ---- Long-format monthly metrics ----
    rows_monthly = []
    for r in results:
        for mo, d in r.monthly.items():
            for met, v in d.items():
                rows_monthly.append({
                    "instrument": r.symbol, "month": mo, "metric": met, "value": v,
                })
    pd.DataFrame(rows_monthly).to_csv(OUT_DIR / "02_monthly_metrics.csv", index=False)

    # ---- H1/H2 split ----
    rows_h = []
    for r in results:
        for met, d in r.h1h2.items():
            rows_h.append({
                "instrument": r.symbol, "metric": met,
                "h1_mean": d["h1_mean"], "h2_mean": d["h2_mean"],
                "delta": d["delta"], "p_value": d["p_value"],
                "h1_n": d.get("h1_n"), "h2_n": d.get("h2_n"),
            })
    pd.DataFrame(rows_h).to_csv(OUT_DIR / "02_h1_h2_split.csv", index=False)

    # ---- Per-instrument scorecard ----
    rows_score = []
    for r in results:
        # Compose direction labels per metric
        dirs = {met: r.trends[met]["direction"] for met in r.trends}
        rows_score.append({
            "instrument": r.symbol,
            "months_observed": len(r.monthly),
            "composite_direction": r.composite_dir,
            "decay_score": r.decay_score,
            "h1_bos_retest_wr_dir": dirs.get("h1_bos_retest_wr"),
            "ob_per_day_dir": dirs.get("ob_per_day"),
            "bos_per_day_dir": dirs.get("bos_per_day"),
            "fvg_per_100_dir": dirs.get("fvg_per_100"),
            "displacement_rate_dir": dirs.get("displacement_rate"),
            "atr_m15_dir": dirs.get("atr_m15"),
            "atr_h1_dir": dirs.get("atr_h1"),
            "vol_persistence_dir": dirs.get("vol_persistence"),
            "ac1_logret_dir": dirs.get("ac1_logret"),
            "hurst_dir": dirs.get("hurst"),
            "sweep_reversal_wr_dir": dirs.get("sweep_reversal_wr"),
            # Headline H1/H2 deltas
            "h1_bos_wr_h1": r.h1h2.get("h1_bos_retest_wr", {}).get("h1_mean"),
            "h1_bos_wr_h2": r.h1h2.get("h1_bos_retest_wr", {}).get("h2_mean"),
            "h1_bos_wr_p": r.h1h2.get("h1_bos_retest_wr", {}).get("p_value"),
            "h1_bos_wr_h1_n": r.h1h2.get("h1_bos_retest_wr", {}).get("h1_n"),
            "h1_bos_wr_h2_n": r.h1h2.get("h1_bos_retest_wr", {}).get("h2_n"),
            "ob_per_day_h1": r.h1h2.get("ob_per_day", {}).get("h1_mean"),
            "ob_per_day_h2": r.h1h2.get("ob_per_day", {}).get("h2_mean"),
            "atr_m15_h1": r.h1h2.get("atr_m15", {}).get("h1_mean"),
            "atr_m15_h2": r.h1h2.get("atr_m15", {}).get("h2_mean"),
        })
    df_score = pd.DataFrame(rows_score).sort_values("decay_score", ascending=False)
    df_score.to_csv(OUT_DIR / "02_per_instrument_decay_scorecard.csv", index=False)

    # ---- Decay clusters ----
    # Cluster instruments by sign-pattern of trends across edge metrics
    rows_cluster = []
    for r in results:
        sig = "".join(
            ("D" if r.trends[met]["direction"] == "DECAYING" else
             "I" if r.trends[met]["direction"] == "IMPROVING" else
             "S" if r.trends[met]["direction"] == "STABLE" else "V")
            for met in ("h1_bos_retest_wr", "ob_per_day", "displacement_rate", "atr_m15", "vol_persistence")
        )
        rows_cluster.append({
            "instrument": r.symbol,
            "edge_pattern": sig,
            "asset_class": _asset_class(r.symbol),
            "decay_score": r.decay_score,
            "composite_direction": r.composite_dir,
        })
    df_clu = pd.DataFrame(rows_cluster).sort_values(["edge_pattern", "decay_score"], ascending=[True, False])
    df_clu.to_csv(OUT_DIR / "02_decay_clusters.csv", index=False)

    # ---- Persist results JSON for narrative ----
    payload = []
    for r in results:
        payload.append({
            "symbol": r.symbol,
            "monthly": r.monthly,
            "h1h2": r.h1h2,
            "trends": r.trends,
            "stability": r.stability,
            "decay_score": r.decay_score,
            "composite_dir": r.composite_dir,
        })
    with open(OUT_DIR / "02_results.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)

    print("DONE.")
    print(f"  scorecard: {OUT_DIR / '02_per_instrument_decay_scorecard.csv'}")
    print(f"  monthly:   {OUT_DIR / '02_monthly_metrics.csv'}")
    print(f"  h1h2:      {OUT_DIR / '02_h1_h2_split.csv'}")
    print(f"  clusters:  {OUT_DIR / '02_decay_clusters.csv'}")


def _asset_class(sym: str) -> str:
    metals = {"XAUUSD", "XAGUSD"}
    crypto = {"BTCUSD", "ETHUSD"}
    indices = {"GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_cash"}
    energy = {"UKOIL_cash", "USOIL_cash"}
    if sym in metals:
        return "METALS"
    if sym in crypto:
        return "CRYPTO"
    if sym in indices:
        return "INDEX"
    if sym in energy:
        return "ENERGY"
    return "FX"


if __name__ == "__main__":
    main()
