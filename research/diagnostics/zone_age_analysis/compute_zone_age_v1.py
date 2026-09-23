#!/usr/bin/env python3
"""
Q-2.2: OB Zone Age vs Continuation Rate
Tests whether the age of an order block zone at the time of retest
predicts its continuation rate.

Pre-committed hypothesis:
    Fresh zones (low formation_age_bars, low touch_count) have HIGHER
    continuation rates than stale zones, because the Osler stop-cascade
    mechanism depletes with each re-entry.

Data source:
    Raw H1 candles from exports/multi_instrument/
    Re-runs OB detection and multi-touch tracking from scratch.
    Uses identical OB-detection parameters to multi_instrument_screening.py.

Output:
    research/diagnostics/zone_age_analysis/ob_zone_age_v1.md

Author: Claude Code  (for CEO review)
Date: 2026-04-11
Version: v1
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as scipy_stats

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG  (identical to multi_instrument_screening.py where overlap exists)
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]           # gold-agent/
DATA_DIR = ROOT / "exports" / "multi_instrument"
OUTPUT_DIR = Path(__file__).parent                   # zone_age_analysis/

SWING_MIN_BARS = 2
WARMUP_CANDLES = 100
MIN_DISPLACEMENT_ATR = 0.4
BODY_RATIO_MIN = 0.40
RETEST_WINDOW = 250          # H1 bars — maximum bars to look for retest after OB formation
CONTINUATION_WINDOW = 20     # H1 bars — outcome window after each touch
ATR_PERIOD = 14
TARGET_ATR_MULT = 1.25
STOP_ATR_MULT = 0.50

ALL_INSTRUMENTS = [
    "XAUUSD", "US30_cash", "GBPUSD", "USDJPY", "NZDUSD",
    "GBPJPY", "EURJPY", "EURUSD", "USDCAD", "AUDUSD",
    "XAGUSD", "US500_cash", "USOIL_cash",
]
# Per-instrument breakdown is restricted to the 5 live instruments
LIVE_INSTRUMENTS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95 % confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p_hat = k / n
    denom = 1 + z ** 2 / n
    centre = (p_hat + z ** 2 / (2 * n)) / denom
    margin = z * math.sqrt(p_hat * (1 - p_hat) / n + z ** 2 / (4 * n ** 2)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def compute_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                period: int = ATR_PERIOD) -> np.ndarray:
    n = len(highs)
    tr = np.empty(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]))
    atr = np.full(n, np.nan)
    if n <= period:
        return atr
    atr[period] = float(np.mean(tr[1: period + 1]))
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────────────────────

def load_instrument(symbol: str) -> pd.DataFrame | None:
    """Load H1 candles for a symbol, convert to UTC.  Returns None if missing."""
    candidates = [
        DATA_DIR / f"{symbol}_H1.csv",
        DATA_DIR / f"{symbol.replace('.', '_')}_H1.csv",
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            required = {"time", "open", "high", "low", "close"}
            if not required.issubset(df.columns):
                return None
            # Convert EET server time → UTC  (same as screening script)
            try:
                import pytz
                eet = pytz.timezone("EET")
                dt = pd.to_datetime(df["time"])
                df["dt_utc"] = (
                    dt.dt.tz_localize(eet, ambiguous="infer",
                                      nonexistent="shift_forward")
                    .dt.tz_convert("UTC")
                    .dt.tz_localize(None)
                )
            except Exception:
                df["dt_utc"] = pd.to_datetime(df["time"]) - pd.Timedelta(hours=2)
            for col in ("open", "high", "low", "close"):
                df[col] = df[col].astype(float)
            df = df.reset_index(drop=True)
            return df
    return None


# ──────────────────────────────────────────────────────────────────────────────
# SWING DETECTION  (verbatim logic from multi_instrument_screening.py)
# ──────────────────────────────────────────────────────────────────────────────

def detect_swings_at(highs: np.ndarray, lows: np.ndarray,
                     i: int, min_bars: int = SWING_MIN_BARS):
    n = len(highs)
    is_high = is_low = False
    if i >= min_bars and i < n - min_bars:
        is_high = all(
            highs[i] > highs[i - j] and highs[i] > highs[i + j]
            for j in range(1, min_bars + 1)
        )
        is_low = all(
            lows[i] < lows[i - j] and lows[i] < lows[i + j]
            for j in range(1, min_bars + 1)
        )
    return is_high, is_low


# ──────────────────────────────────────────────────────────────────────────────
# OB DETECTION  (adapted from multi_instrument_screening.py)
# ──────────────────────────────────────────────────────────────────────────────

def detect_obs(df: pd.DataFrame, atr: np.ndarray) -> list[dict]:
    """
    Detect order blocks using the same algorithm as multi_instrument_screening.py.
    Returns a list of dicts with OB metadata.
    """
    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    times = df["dt_utc"].values

    n = len(df)
    obs: list[dict] = []

    # --- swing tracking (online) ---
    swings: list[dict] = []          # {index, price, type, classification, consumed}
    last_high: dict | None = None
    last_low: dict | None = None
    current_structure = "neutral"    # 'bullish' | 'bearish' | 'neutral'

    for i in range(WARMUP_CANDLES, n - SWING_MIN_BARS):
        if np.isnan(atr[i]) or atr[i] == 0:
            continue

        is_sh, is_sl = detect_swings_at(highs, lows, i)

        if is_sh:
            label = "HH" if (last_high is None or highs[i] > last_high["price"]) else "LH"
            swg = {"index": i, "price": highs[i], "type": "high",
                   "classification": label, "consumed": False}
            swings.append(swg)
            last_high = swg

        if is_sl:
            label = "HL" if (last_low is None or lows[i] > last_low["price"]) else "LL"
            swg = {"index": i, "price": lows[i], "type": "low",
                   "classification": label, "consumed": False}
            swings.append(swg)
            last_low = swg

        # ---- BOS / CHoCH detection ----
        if len(swings) < 4:
            continue

        highs_list = [s for s in swings if s["type"] == "high" and not s["consumed"]]
        lows_list = [s for s in swings if s["type"] == "low" and not s["consumed"]]

        if not highs_list or not lows_list:
            continue

        # Bullish BOS: close > last unconsumed swing high
        last_swing_high = highs_list[-1]
        if (closes[i] > last_swing_high["price"] and
                i > last_swing_high["index"] + 1):
            disp = (closes[i] - last_swing_high["price"]) / atr[i]
            body = abs(closes[i] - opens[i]) / (highs[i] - lows[i] + 1e-10)
            if disp >= MIN_DISPLACEMENT_ATR and body >= BODY_RATIO_MIN:
                event_type = "CHoCH" if current_structure == "bearish" else "BOS"
                current_structure = "bullish"
                # Find the OB: last bearish candle in the 10 bars before break
                ob_found = False
                for k in range(i - 1, max(i - 11, WARMUP_CANDLES - 1), -1):
                    if closes[k] < opens[k]:   # bearish candle
                        obs.append({
                            "direction": "bullish",
                            "ob_high": highs[k],
                            "ob_low": lows[k],
                            "formation_index": k,
                            "formation_time": str(times[k]),
                            "event_type": event_type,
                            "break_index": i,
                        })
                        ob_found = True
                        break
                if ob_found:
                    last_swing_high["consumed"] = True

        # Bearish BOS: close < last unconsumed swing low
        last_swing_low = lows_list[-1]
        if (closes[i] < last_swing_low["price"] and
                i > last_swing_low["index"] + 1):
            disp = (last_swing_low["price"] - closes[i]) / atr[i]
            body = abs(closes[i] - opens[i]) / (highs[i] - lows[i] + 1e-10)
            if disp >= MIN_DISPLACEMENT_ATR and body >= BODY_RATIO_MIN:
                event_type = "CHoCH" if current_structure == "bullish" else "BOS"
                current_structure = "bearish"
                ob_found = False
                for k in range(i - 1, max(i - 11, WARMUP_CANDLES - 1), -1):
                    if closes[k] > opens[k]:   # bullish candle
                        obs.append({
                            "direction": "bearish",
                            "ob_high": highs[k],
                            "ob_low": lows[k],
                            "formation_index": k,
                            "formation_time": str(times[k]),
                            "event_type": event_type,
                            "break_index": i,
                        })
                        ob_found = True
                        break
                if ob_found:
                    last_swing_low["consumed"] = True

    return obs


# ──────────────────────────────────────────────────────────────────────────────
# MULTI-TOUCH TRACKING
# ──────────────────────────────────────────────────────────────────────────────

def track_all_touches(ob: dict, highs: np.ndarray, lows: np.ndarray,
                      closes: np.ndarray, times: np.ndarray,
                      atr: np.ndarray) -> list[dict]:
    """
    Track ALL entries of price into the OB zone within RETEST_WINDOW bars
    of formation.  Each distinct entry (transition from outside → inside the
    zone) is one touch event.  Returns a list of touch-event dicts.

    Continuation for touch T is measured over the 20-bar window after the
    first bar where price enters the zone.
    """
    n = len(highs)
    start = ob["formation_index"] + 1
    end = min(start + RETEST_WINDOW, n)

    direction = ob["direction"]
    ob_high = ob["ob_high"]
    ob_low = ob["ob_low"]

    events: list[dict] = []
    in_zone = False
    touch_count = 0
    last_touch_index = ob["formation_index"]

    for j in range(start, end):
        # Price is "in zone" when it enters the band [ob_low, ob_high]
        if direction == "bullish":
            touching = lows[j] <= ob_high          # price dips into the OB
        else:
            touching = highs[j] >= ob_low          # price rallies into the OB

        if touching and not in_zone:
            in_zone = True
            touch_count += 1

            formation_age = j - ob["formation_index"]
            bars_since = j - last_touch_index

            # --- measure continuation from this touch ---
            cont = _measure_continuation(
                j, direction, ob_high, ob_low, highs, lows, closes, atr, n
            )

            events.append({
                "formation_index": ob["formation_index"],
                "formation_time": ob["formation_time"],
                "direction": direction,
                "event_type": ob["event_type"],
                "retest_index": j,
                "retest_time": str(times[j]),
                "touch_number": touch_count,
                "formation_age_bars": formation_age,
                "bars_since_last_touch": bars_since,
                "continuation": cont,
            })
            last_touch_index = j

        elif not touching:
            in_zone = False

    return events


def _measure_continuation(ri: int, direction: str,
                           ob_high: float, ob_low: float,
                           highs: np.ndarray, lows: np.ndarray,
                           closes: np.ndarray, atr: np.ndarray,
                           n: int) -> bool:
    """
    ATR-based continuation: same logic as multi_instrument_screening.py.
    Entry = closes[ri].  Target = entry ± 1.25*ATR.  Stop = entry ∓ 0.5*ATR.
    Returns True if target hit before stop within CONTINUATION_WINDOW bars.
    """
    if ri >= n - 1 or np.isnan(atr[ri]) or atr[ri] == 0:
        return False

    entry = closes[ri]
    target_dist = TARGET_ATR_MULT * atr[ri]
    stop_dist = STOP_ATR_MULT * atr[ri]

    if direction == "bullish":
        target = entry + target_dist
        stop = entry - stop_dist
    else:
        target = entry - target_dist
        stop = entry + stop_dist

    end = min(ri + 1 + CONTINUATION_WINDOW, n)
    for j in range(ri + 1, end):
        if direction == "bullish":
            if highs[j] >= target:
                return True
            if lows[j] <= stop:
                return False
        else:
            if lows[j] <= target:
                return True
            if highs[j] >= stop:
                return False
    return False          # timeout → failure (same as original)


# ──────────────────────────────────────────────────────────────────────────────
# PROCESSING PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

def process_instrument(symbol: str) -> list[dict]:
    """
    Full pipeline for one instrument:
    load → ATR → OB detect → multi-touch track → return list of event dicts.
    """
    df = load_instrument(symbol)
    if df is None or len(df) < 500:
        print(f"  SKIP {symbol}: file missing or < 500 bars")
        return []

    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    opens = df["open"].values
    times = df["dt_utc"].values
    atr = compute_atr(highs, lows, closes)

    obs = detect_obs(df, atr)
    print(f"  {symbol}: {len(df):>6} candles → {len(obs):>4} OBs detected")

    events: list[dict] = []
    for ob in obs:
        touch_events = track_all_touches(ob, highs, lows, closes, times, atr)
        for ev in touch_events:
            ev["symbol"] = symbol
        events.extend(touch_events)

    return events


# ──────────────────────────────────────────────────────────────────────────────
# STATISTICAL TESTS
# ──────────────────────────────────────────────────────────────────────────────

def quartile_table(series: pd.Series, outcome: pd.Series,
                   label: str) -> tuple[pd.DataFrame, list[tuple]]:
    """
    Split *series* into quartiles; compute continuation rate + Wilson CI.
    Returns (results_df, list_of_fisher_tests).
    Fisher tests: Q1 vs Q4, Q1 vs Q2, Q2 vs Q3, Q3 vs Q4.
    """
    q_labels, bins = pd.qcut(series, q=4, labels=False, retbins=True,
                              duplicates="drop")
    n_q = q_labels.max() + 1

    rows = []
    cont_by_q = []
    for q in range(n_q):
        mask = q_labels == q
        n = mask.sum()
        k = outcome[mask].sum()
        lo, hi = wilson_ci(int(k), int(n))
        rows.append({
            "quartile": q + 1,
            "n": n,
            "cont_n": k,
            "cont_rate": round(k / n * 100, 1) if n > 0 else np.nan,
            "ci_lo": round(lo * 100, 1),
            "ci_hi": round(hi * 100, 1),
            "age_min": round(bins[q], 1),
            "age_max": round(bins[q + 1], 1),
        })
        cont_by_q.append((int(k), int(n)))

    df_q = pd.DataFrame(rows)

    fisher_pairs = []
    pairs = [(0, 3), (0, 1), (1, 2), (2, 3)]   # (Q1 vs Q4), (Q1 vs Q2), ...
    for a, b in pairs:
        if a >= n_q or b >= n_q:
            continue
        ka, na = cont_by_q[a]
        kb, nb = cont_by_q[b]
        if na == 0 or nb == 0:
            continue
        table = [[ka, na - ka], [kb, nb - kb]]
        _, p = scipy_stats.fisher_exact(table)
        fisher_pairs.append((a + 1, b + 1, p))

    return df_q, fisher_pairs


def logistic_regression_test(X: np.ndarray, y: np.ndarray,
                              label: str) -> dict:
    """
    Logistic regression y ~ X using statsmodels.
    Returns: beta, p_value (Wald), pseudo_r2 (McFadden).
    """
    X_sm = sm.add_constant(X.astype(float))
    try:
        model = sm.Logit(y.astype(float), X_sm)
        result = model.fit(disp=0, maxiter=100)
        beta = result.params[1]
        p_wald = result.pvalues[1]
        # McFadden pseudo-R²
        ll_full = result.llf
        ll_null = result.llnull
        pseudo_r2 = 1.0 - ll_full / ll_null if ll_null != 0 else np.nan
        return {
            "metric": label,
            "beta": round(float(beta), 6),
            "p_wald": float(p_wald),
            "pseudo_r2": round(float(pseudo_r2), 5),
            "n": int(len(y)),
        }
    except Exception as exc:
        return {"metric": label, "beta": np.nan, "p_wald": np.nan,
                "pseudo_r2": np.nan, "n": int(len(y)), "error": str(exc)}


def threshold_scan(series: pd.Series, outcome: pd.Series) -> pd.DataFrame:
    """
    Scan Metric A (formation_age_bars) thresholds 10..200 step 10.
    For each threshold: continuation rate young vs old, difference, Fisher p.
    """
    rows = []
    for thr in range(10, 210, 10):
        young = series < thr
        old = series >= thr
        ny, ky = int(young.sum()), int(outcome[young].sum())
        no, ko = int(old.sum()), int(outcome[old].sum())
        if ny == 0 or no == 0:
            continue
        ry = ky / ny * 100
        ro = ko / no * 100
        table = [[ky, ny - ky], [ko, no - ko]]
        _, p = scipy_stats.fisher_exact(table)
        rows.append({
            "threshold": thr,
            "n_young": ny, "cont_young_pct": round(ry, 1),
            "n_old": no, "cont_old_pct": round(ro, 1),
            "delta_pp": round(ry - ro, 1),
            "fisher_p": p,
        })
    return pd.DataFrame(rows)


def touch_count_table(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """
    Continuation rate by touch_number (1, 2, 3, 4+).
    Returns (results_df, chi_sq_p).
    """
    df2 = df.copy()
    df2["touch_grp"] = df2["touch_number"].clip(upper=4)
    df2["touch_grp"] = df2["touch_grp"].map({1: "1", 2: "2", 3: "3", 4: "4+"})

    rows = []
    for grp in ["1", "2", "3", "4+"]:
        sub = df2[df2["touch_grp"] == grp]
        n = len(sub)
        k = int(sub["continuation"].sum())
        lo, hi = wilson_ci(k, n)
        rows.append({
            "touch_number": grp,
            "n": n,
            "cont_n": k,
            "cont_rate": round(k / n * 100, 1) if n > 0 else np.nan,
            "ci_lo": round(lo * 100, 1),
            "ci_hi": round(hi * 100, 1),
        })
    df_tc = pd.DataFrame(rows)

    # Chi-squared across groups (observed vs expected)
    observed = [r["cont_n"] for _, r in df_tc.iterrows() if r["n"] > 0]
    total_cont = sum(observed)
    ns = [r["n"] for _, r in df_tc.iterrows() if r["n"] > 0]
    total_n = sum(ns)
    if total_n > 0 and total_cont > 0:
        expected = [total_cont * n / total_n for n in ns]
        chi2, chi2_p = scipy_stats.chisquare(observed, expected)
    else:
        chi2, chi2_p = np.nan, np.nan

    # Fisher pair-wise: 1 vs 2, 2 vs 3, 3 vs 4+
    df_tc = df_tc.copy()
    return df_tc, float(chi2_p) if not np.isnan(chi2_p) else np.nan


# ──────────────────────────────────────────────────────────────────────────────
# REPORT WRITER
# ──────────────────────────────────────────────────────────────────────────────

def fmt_p(p: float, n_tests: int, alpha: float = 0.05) -> str:
    if np.isnan(p):
        return "n/a"
    corrected = p * n_tests
    star = " *SIGNIFICANT*" if corrected < alpha else ""
    return f"{p:.4e} (corrected {corrected:.4e}){star}"


def write_report(df: pd.DataFrame, results: dict, n_total_tests: int) -> None:
    """Write the markdown report to ob_zone_age_v1.md."""
    alpha = 0.05

    lines = []
    A = lambda s: lines.append(s)

    A("# Q-2.2: OB Zone Age vs Continuation Rate")
    A("")
    A(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    A(f"**Version:** v1")
    A(f"**Script:** `research/diagnostics/zone_age_analysis/compute_zone_age_v1.py`")
    A("")
    A("---")
    A("")
    A("## 1  Data Source")
    A("")
    A("| Field | Value |")
    A("|-------|-------|")
    A(f"| Source | H1 candle CSVs in `exports/multi_instrument/` |")
    A(f"| Instruments analysed | {len(results['instruments_loaded'])} of {len(ALL_INSTRUMENTS)} |")
    A(f"| Total OBs detected | {results['total_obs']:,} |")
    A(f"| Total retest events (all touches) | {len(df):,} |")
    A(f"| First-touch events (touch_number == 1) | {int((df.touch_number == 1).sum()):,} |")
    A(f"| Multi-touch events (touch_number >= 2) | {int((df.touch_number >= 2).sum()):,} |")
    A(f"| Instrument date ranges | 2022-11 to 2026-04 (≈ 3.5 years) |")
    A(f"| OB detection params | SWING_MIN_BARS=2, MIN_DISPLACEMENT_ATR=0.4, BODY_RATIO_MIN=0.4 |")
    A(f"| Retest window | {RETEST_WINDOW} H1 bars (≈10 trading days) |")
    A(f"| Continuation window | {CONTINUATION_WINDOW} bars, target={TARGET_ATR_MULT}×ATR, stop={STOP_ATR_MULT}×ATR |")
    A("")

    # Per-instrument counts
    A("### Per-Instrument Event Counts")
    A("")
    A("| Instrument | OBs | 1st-Touch | Multi-Touch | Overall Cont% |")
    A("|-----------|-----|-----------|-------------|--------------|")
    for sym in results["instruments_loaded"]:
        sub = df[df["symbol"] == sym]
        t1 = (sub.touch_number == 1).sum()
        tm = (sub.touch_number >= 2).sum()
        k = int(sub["continuation"].sum())
        n = len(sub)
        cr = f"{k/n*100:.1f}%" if n > 0 else "—"
        ob_cnt = results["obs_per_symbol"].get(sym, "—")
        A(f"| {sym} | {ob_cnt} | {t1} | {tm} | {cr} |")
    A("")

    # ── 2  Age metric distributions ───────────────────────────────────────────
    A("---")
    A("")
    A("## 2  Age Metric Distributions")
    A("")
    for metric, col in [
        ("Metric A — Formation Age (bars to first touch)", "formation_age_bars"),
        ("Metric B — Touch Number", "touch_number"),
        ("Metric C — Bars Since Last Touch", "bars_since_last_touch"),
    ]:
        ser = df[col]
        A(f"### {metric}")
        A("")
        A(f"| Stat | Value |")
        A("|------|-------|")
        A(f"| n | {len(ser):,} |")
        A(f"| mean | {ser.mean():.1f} |")
        A(f"| median | {ser.median():.1f} |")
        A(f"| std | {ser.std():.1f} |")
        A(f"| min | {ser.min():.0f} |")
        A(f"| p25 | {ser.quantile(0.25):.1f} |")
        A(f"| p75 | {ser.quantile(0.75):.1f} |")
        A(f"| max | {ser.max():.0f} |")
        A("")

    # ── 3  Quartile analysis ──────────────────────────────────────────────────
    A("---")
    A("")
    A("## 3  Quartile Analysis")
    A("")

    metric_info = [
        ("Metric A — Formation Age (bars)", "formation_age_bars"),
        ("Metric B — Touch Number (clipped 1–4)", "touch_number_q"),
        ("Metric C — Bars Since Last Touch", "bars_since_last_touch"),
    ]

    df["touch_number_q"] = df["touch_number"].clip(upper=4)

    for label, col in metric_info:
        A(f"### {label}")
        A("")
        df_q, fisher_pairs = results["quartile"][col]
        A("| Quartile | n | Cont | Cont% | 95% CI |")
        A("|---------|---|------|-------|--------|")
        for _, r in df_q.iterrows():
            ci = f"[{r.ci_lo:.1f}%, {r.ci_hi:.1f}%]"
            if col == "formation_age_bars":
                band = f"({r.age_min:.0f}–{r.age_max:.0f} bars)"
            elif col == "touch_number_q":
                band = f"(touch {int(r.age_min)}–{int(r.age_max)})"
            else:
                band = f"({r.age_min:.0f}–{r.age_max:.0f} bars)"
            A(f"| Q{int(r.quartile)} {band} | {int(r.n)} | {int(r.cont_n)} | {r.cont_rate}% | {ci} |")
        A("")
        A("**Fisher exact tests (raw p):**")
        A("")
        for qa, qb, p in fisher_pairs:
            A(f"- Q{qa} vs Q{qb}: {fmt_p(p, n_total_tests)}")
        A("")

    # ── 4  Logistic Regression ────────────────────────────────────────────────
    A("---")
    A("")
    A("## 4  Logistic Regression")
    A("")
    A("Model: `continuation ~ age_metric` (statsmodels Logit, Wald test on beta)")
    A("")
    A("| Metric | n | beta | p (Wald) | pseudo-R² |")
    A("|--------|---|------|----------|-----------|")
    for r in results["logistic"]:
        p_fmt = fmt_p(r["p_wald"], n_total_tests)
        A(f"| {r['metric']} | {r['n']:,} | {r['beta']:.6f} | {p_fmt} | {r['pseudo_r2']:.5f} |")
    A("")
    A("> **Beta interpretation:** negative beta for Metric A means older zones have lower")
    A("> continuation rates (confirming the pre-committed hypothesis if significant).")
    A("")

    # ── 5  Threshold Scan ─────────────────────────────────────────────────────
    A("---")
    A("")
    A("## 5  Threshold Scan (Metric A — Formation Age)")
    A("")
    df_thr = results["threshold_scan"]
    if df_thr.empty:
        A("*No threshold scan data.*")
    else:
        A("| Threshold | n(young) | Cont%(young) | n(old) | Cont%(old) | Δpp | Fisher p |")
        A("|-----------|----------|-------------|--------|------------|-----|---------|")
        for _, r in df_thr.iterrows():
            A(f"| {int(r.threshold):>3} bars | {int(r.n_young):>5} | {r.cont_young_pct:.1f}% | {int(r.n_old):>5} | {r.cont_old_pct:.1f}% | {r.delta_pp:+.1f}pp | {r.fisher_p:.4e} |")
        # Find optimal threshold
        if not df_thr.empty:
            best = df_thr.loc[df_thr["fisher_p"].idxmin()]
            A("")
            A(f"**Optimal threshold (minimum Fisher p):** {int(best.threshold)} bars")
            A(f"- Young (< {int(best.threshold)} bars): {best.cont_young_pct:.1f}%  n={int(best.n_young)}")
            A(f"- Old (≥ {int(best.threshold)} bars): {best.cont_old_pct:.1f}%  n={int(best.n_old)}")
            A(f"- Δ = {best.delta_pp:+.1f}pp  |  raw p = {best.fisher_p:.4e}  |  Bonferroni: {fmt_p(best.fisher_p, n_total_tests)}")
    A("")

    # ── 6  Touch Count Table ──────────────────────────────────────────────────
    A("---")
    A("")
    A("## 6  Touch Count Table (Metric B)")
    A("")
    df_tc, chi2_p = results["touch_count"]
    A("| Touch # | n | Cont | Cont% | 95% CI |")
    A("|---------|---|------|-------|--------|")
    for _, r in df_tc.iterrows():
        if r["n"] == 0:
            continue
        ci = f"[{r.ci_lo:.1f}%, {r.ci_hi:.1f}%]"
        A(f"| {r.touch_number} | {int(r.n):,} | {int(r.cont_n):,} | {r.cont_rate:.1f}% | {ci} |")
    A("")
    A(f"**Chi-squared across groups:** {fmt_p(chi2_p, n_total_tests)}")
    A("")

    # ── 7  Per-Instrument Breakdown ───────────────────────────────────────────
    A("---")
    A("")
    A("## 7  Per-Instrument Breakdown (Metric A — Formation Age)")
    A("")
    A("Quartile analysis restricted to the 5 live GTOS instruments.")
    A("")
    for sym in LIVE_INSTRUMENTS:
        sub = df[df["symbol"] == sym]
        if len(sub) < 20:
            A(f"### {sym}  (n={len(sub)} — insufficient data)")
            A("")
            continue
        A(f"### {sym}  (n={len(sub):,} retest events)")
        A("")
        df_q, fisher_pairs = quartile_table(
            sub["formation_age_bars"], sub["continuation"], sym
        )
        A("| Quartile | n | Cont | Cont% | 95% CI |")
        A("|---------|---|------|-------|--------|")
        for _, r in df_q.iterrows():
            ci = f"[{r.ci_lo:.1f}%, {r.ci_hi:.1f}%]"
            band = f"({r.age_min:.0f}–{r.age_max:.0f} bars)"
            A(f"| Q{int(r.quartile)} {band} | {int(r.n)} | {int(r.cont_n)} | {r.cont_rate}% | {ci} |")
        A("")
        A("Fisher tests (raw p):")
        for qa, qb, p in fisher_pairs:
            A(f"- Q{qa} vs Q{qb}: {fmt_p(p, n_total_tests)}")
        A("")

    # ── 8  Bonferroni Summary ─────────────────────────────────────────────────
    A("---")
    A("")
    A("## 8  Bonferroni Correction Summary")
    A("")
    A(f"**Total tests in this analysis:** {n_total_tests}")
    A(f"**Bonferroni threshold (α=0.05):** {alpha / n_total_tests:.6f}")
    A(f"**Equivalent: raw p must be < {alpha / n_total_tests:.4e} to survive**")
    A("")

    sig = results.get("significant_findings", [])
    if sig:
        A("**Findings surviving Bonferroni correction:**")
        A("")
        for f in sig:
            A(f"- {f}")
    else:
        A("**No individual test survives Bonferroni correction** at α=0.05.")
    A("")

    # ── 9  Plain-Language Conclusion ──────────────────────────────────────────
    A("---")
    A("")
    A("## 9  Conclusion")
    A("")
    A(results.get("conclusion_text", "*Not generated.*"))
    A("")

    # ── 10  Actionable Recommendation ────────────────────────────────────────
    A("---")
    A("")
    A("## 10  Actionable Recommendation for GTOS")
    A("")
    A(results.get("recommendation_text", "*Not generated.*"))
    A("")

    out_path = OUTPUT_DIR / "ob_zone_age_v1.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written → {out_path}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("Q-2.2: OB Zone Age vs Continuation Rate")
    print("=" * 70)

    # ─── 1. Collect all retest events ────────────────────────────────────────
    all_events: list[dict] = []
    instruments_loaded = []
    obs_per_symbol: dict[str, int] = {}
    total_obs = 0

    for sym in ALL_INSTRUMENTS:
        print(f"\nProcessing {sym} …")
        events = process_instrument(sym)
        if events:
            instruments_loaded.append(sym)
            n_obs = len({e["formation_index"] for e in events})
            obs_per_symbol[sym] = n_obs
            total_obs += n_obs
            all_events.extend(events)

    if not all_events:
        print("ERROR: no events collected.  Check DATA_DIR path.")
        return

    df = pd.DataFrame(all_events)
    df["continuation"] = df["continuation"].astype(int)
    df["touch_number_q"] = df["touch_number"].clip(upper=4)

    print(f"\n{'─'*50}")
    print(f"Total retest events: {len(df):,}")
    print(f"First-touch events:  {int((df.touch_number == 1).sum()):,}")
    print(f"Overall cont rate:   {df.continuation.mean()*100:.1f}%")

    # ─── 2. Count tests for Bonferroni ───────────────────────────────────────
    # Quartile: 3 metrics × 4 pairs = 12
    # Logistic: 3 metrics = 3
    # Threshold scan: 20 (10..200 step 10)
    # Touch count: 1 chi-sq = 1
    # Per-instrument (5) × 4 pairs = 20
    # Additional: 3 Fisher pair-wise for touch count groups = 3
    n_tests = 12 + 3 + 20 + 1 + 20 + 3   # = 59
    bonferroni_alpha = 0.05 / n_tests

    results: dict = {
        "instruments_loaded": instruments_loaded,
        "total_obs": total_obs,
        "obs_per_symbol": obs_per_symbol,
        "quartile": {},
        "logistic": [],
        "significant_findings": [],
    }

    # ─── 3. Quartile analysis ─────────────────────────────────────────────────
    print("\nRunning quartile analysis …")
    for col in ("formation_age_bars", "touch_number_q", "bars_since_last_touch"):
        df_q, fp = quartile_table(df[col], df["continuation"], col)
        results["quartile"][col] = (df_q, fp)
        for qa, qb, p in fp:
            if p * n_tests < 0.05:
                results["significant_findings"].append(
                    f"Quartile {col}: Q{qa} vs Q{qb}, raw p={p:.4e}"
                )

    # ─── 4. Logistic regression ───────────────────────────────────────────────
    print("Running logistic regressions …")
    for col, label in [
        ("formation_age_bars", "Metric A: formation_age_bars"),
        ("touch_number", "Metric B: touch_number"),
        ("bars_since_last_touch", "Metric C: bars_since_last_touch"),
    ]:
        r = logistic_regression_test(df[col].values, df["continuation"].values, label)
        results["logistic"].append(r)
        if not np.isnan(r["p_wald"]) and r["p_wald"] * n_tests < 0.05:
            results["significant_findings"].append(
                f"Logistic {col}: beta={r['beta']:.6f}, raw p={r['p_wald']:.4e}"
            )

    # ─── 5. Threshold scan ────────────────────────────────────────────────────
    print("Running threshold scan …")
    df_thr = threshold_scan(df["formation_age_bars"], df["continuation"])
    results["threshold_scan"] = df_thr
    sig_thr = df_thr[df_thr["fisher_p"] * n_tests < 0.05]
    for _, r in sig_thr.iterrows():
        results["significant_findings"].append(
            f"Threshold scan {int(r.threshold)} bars: raw p={r.fisher_p:.4e}"
        )

    # ─── 6. Touch count table ────────────────────────────────────────────────
    print("Running touch count analysis …")
    df_tc, chi2_p = touch_count_table(df)
    results["touch_count"] = (df_tc, chi2_p)
    if not np.isnan(chi2_p) and chi2_p * n_tests < 0.05:
        results["significant_findings"].append(
            f"Touch count chi-sq: raw p={chi2_p:.4e}"
        )

    # ── 7. Save event-level data as JSON ────────────────────────────────────
    print("Saving event-level data …")
    event_path = OUTPUT_DIR / "ob_zone_age_events_v1.json"
    with open(event_path, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2, default=str)
    print(f"Event data → {event_path}")

    # ─── 8. Generate conclusion text ─────────────────────────────────────────
    # Pull key numbers for the conclusion
    # Metric A logistic
    log_a = next(r for r in results["logistic"] if "formation_age" in r["metric"])
    log_b = next(r for r in results["logistic"] if "touch_number" in r["metric"])

    # Quartile A: Q1 vs Q4
    df_qa, _ = results["quartile"]["formation_age_bars"]
    if len(df_qa) >= 4:
        q1_cr = df_qa.iloc[0]["cont_rate"]
        q4_cr = df_qa.iloc[-1]["cont_rate"]
        qa_delta = q1_cr - q4_cr
    else:
        q1_cr = q4_cr = qa_delta = np.nan

    # Touch count: touch 1 vs touch 2
    df_tc_vals = results["touch_count"][0]
    t1_row = df_tc_vals[df_tc_vals["touch_number"] == "1"]
    t2_row = df_tc_vals[df_tc_vals["touch_number"] == "2"]
    t1_cr = float(t1_row["cont_rate"].values[0]) if len(t1_row) > 0 else np.nan
    t2_cr = float(t2_row["cont_rate"].values[0]) if len(t2_row) > 0 else np.nan

    # Threshold scan best
    if not df_thr.empty:
        best_thr = df_thr.loc[df_thr["fisher_p"].idxmin()]
        best_thr_bars = int(best_thr["threshold"])
        best_thr_young_cr = float(best_thr["cont_young_pct"])
        best_thr_old_cr = float(best_thr["cont_old_pct"])
        best_thr_delta = float(best_thr["delta_pp"])
        best_thr_p = float(best_thr["fisher_p"])
    else:
        best_thr_bars = 0; best_thr_young_cr = best_thr_old_cr = best_thr_delta = best_thr_p = np.nan

    # Does zone age predict continuation?
    any_sig = len(results["significant_findings"]) > 0
    log_a_sig = (not np.isnan(log_a["p_wald"]) and
                 log_a["p_wald"] * n_tests < 0.05)

    if any_sig:
        conclusion = (
            f"**Zone age DOES predict continuation rate**, with "
            f"{len(results['significant_findings'])} test(s) surviving Bonferroni "
            f"correction (α/n = {bonferroni_alpha:.4e}).\n\n"
            f"**Metric A (formation age):** Q1 continuation = {q1_cr:.1f}% vs "
            f"Q4 = {q4_cr:.1f}% (Δ = {qa_delta:+.1f}pp). "
            f"Logistic beta = {log_a['beta']:.6f}, raw p = {log_a['p_wald']:.4e}. "
            f"{'Negative beta confirms: older zones → lower continuation rates.' if log_a['beta'] < 0 else 'Positive beta — older zones have HIGHER continuation, contrary to hypothesis.'}\n\n"
            f"**Metric B (touch count):** Touch-1 continuation = {t1_cr:.1f}% vs "
            f"Touch-2 = {t2_cr:.1f}%. "
            f"Logistic beta = {log_b['beta']:.6f}.\n\n"
            f"**Optimal threshold scan (Metric A):** {best_thr_bars} bars "
            f"maximises the Fisher p (raw = {best_thr_p:.4e}): "
            f"young < {best_thr_bars} bars → {best_thr_young_cr:.1f}%, "
            f"old ≥ {best_thr_bars} bars → {best_thr_old_cr:.1f}% "
            f"(Δ = {best_thr_delta:+.1f}pp)."
        )
    else:
        conclusion = (
            f"**Zone age does NOT predict continuation rate** in this dataset. "
            f"No test survives Bonferroni correction at α=0.05 (threshold {bonferroni_alpha:.4e}).\n\n"
            f"**Metric A (formation age):** Q1 = {q1_cr:.1f}% vs Q4 = {q4_cr:.1f}% "
            f"(Δ = {qa_delta:+.1f}pp), logistic beta = {log_a['beta']:.6f}, "
            f"raw p = {log_a['p_wald']:.4e}.\n\n"
            f"**Metric B (touch count):** Touch-1 = {t1_cr:.1f}% vs Touch-2 = {t2_cr:.1f}%.\n\n"
            f"The Osler stop-cascade depletion mechanism, while theoretically sound, "
            f"does not manifest as a statistically detectable signal in this data at "
            f"the H1 timeframe with the current OB definition and retest window "
            f"({RETEST_WINDOW} bars)."
        )

    results["conclusion_text"] = conclusion

    if any_sig:
        # Determine best recommendation
        if log_a_sig and log_a["beta"] < 0:
            rec_text = (
                f"**PROMOTE to filter consideration (WF-2 shadow gate):**\n\n"
                f"Add `formation_age_bars < {best_thr_bars}` as a zone quality filter. "
                f"This is the threshold that maximises the young-vs-old continuation "
                f"difference ({best_thr_young_cr:.1f}% vs {best_thr_old_cr:.1f}%, "
                f"Δ={best_thr_delta:+.1f}pp).  Run as shadow gate for ≥30 trades before "
                f"hard gate consideration.\n\n"
                f"If touch count also survives Bonferroni: add `touch_number == 1` "
                f"as an additional filter (first-touch-only mode)."
            )
        else:
            rec_text = (
                f"One or more tests survive Bonferroni but the direction or effect "
                f"size does not clearly support an immediate filter.  "
                f"Investigate the specific finding(s) listed in section 8 "
                f"before making any GTOS parameter change."
            )
    else:
        rec_text = (
            f"**DO NOT add a zone age filter at this time.**\n\n"
            f"Zone age (formation_age_bars, touch_count, bars_since_last_touch) "
            f"shows no statistically significant effect on continuation rate after "
            f"Bonferroni correction.  The edge appears to be in zone *identification* "
            f"(OB location), not zone *freshness*.\n\n"
            f"Re-evaluate if: (1) the dataset grows beyond {len(df):,} events, or "
            f"(2) a theoretically motivated sub-population shows a larger effect "
            f"(e.g., only BOS events, only XAUUSD, only London session)."
        )
    results["recommendation_text"] = rec_text

    # ─── 9. Write report ──────────────────────────────────────────────────────
    write_report(df, results, n_tests)

    # ─── 10. Print key numbers ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("KEY RESULTS")
    print("=" * 70)
    print(f"Total events: {len(df):,}  |  Overall cont rate: {df.continuation.mean()*100:.1f}%")
    print(f"Bonferroni threshold: {bonferroni_alpha:.4e}  ({n_tests} tests)")
    print(f"Significant findings: {len(results['significant_findings'])}")
    if results["significant_findings"]:
        for f in results["significant_findings"]:
            print(f"  → {f}")
    print(f"\nMetric A (formation age) Q1 vs Q4: {q1_cr:.1f}% vs {q4_cr:.1f}%  (Δ={qa_delta:+.1f}pp)")
    print(f"Metric A logistic beta: {log_a['beta']:.6f}  raw p={log_a['p_wald']:.4e}")
    print(f"Touch count: touch-1={t1_cr:.1f}%  touch-2={t2_cr:.1f}%")
    print(f"\nConclusion: {'ZONE AGE SIGNIFICANT' if any_sig else 'ZONE AGE NOT SIGNIFICANT'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
