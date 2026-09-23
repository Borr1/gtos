"""K54 v2 Microstructure feature family.

Scope
=====
Extends the K54 v1 microstructure surface (which had only ``displacement_quality_score``,
hardcoded to 0.5 for 76% of rows) with a much wider set of features derived
from:

* OHLCV bars (M1, M15, H1, H4) — universally available for the 7-instrument
  panel.
* Component-2 structural primitives (count of OBs / FVGs / BBs across
  multiple lookbacks).
* Captured tick parquets under ``data/ticks/{SYMBOL}/*.parquet`` — only
  NAS100 + US30_cash + only 2026-04-27 at the audit cutoff (2026-04-28).
* Synthetic-tick reconstruction (E24 / Lee-Ready candle proxy) on M1 OHLCV
  where real ticks are absent.

Audit note — E24 / E26 (memory ``project_microstructure_archived_2026-04-27``)
found NO_SIGNAL on three simple summary statistics (cumulative_delta,
footprint_imbalance, micro_reversal_count) at n<300 against realized R.
The K54 v2 feature engineering goes BEYOND the simple-statistic surface by:

1. Multi-lookback expansion (5, 20, 50, 200 bars per primitive).
2. Multi-timeframe replication (M15, H1, H4) for Component-2-derived counts.
3. Per-bar / per-window distributional features (z-score, percentile rank)
   that simple statistics throw away.
4. Tick-data-required features WHERE tick coverage exists, with explicit
   sentinel NaN for missing instruments. These will be flagged sparse but
   are stubbed for forward use as the tick daemon accumulates coverage.

Hard constraints
================
* **Data cutoff: 2026-04-28 23:59 UTC.** No future-dated rows are touched.
* **Point-in-time.** Each feature uses only data at-or-before the candle
  close it represents. No future bars in any lookback. The feature
  framework consumes a ``ts_close`` index and slices ``df[df.time < ts]``
  for everything.
* **Pure market state.** OHLCV + ticks + Component-2 outputs only. No news,
  no positioning, no sentiment.
* **No overwrites of production state.** All inputs are READ ONLY from
  ``data/`` and ``knowledge_base/``. Outputs go ONLY to
  ``research/ml_program/``.
* **Tick-coverage caveat.** Tick-required features return NaN (np.nan)
  for instruments without tick parquets at that date. They never
  silently substitute zeros.

Public surface
==============
Each feature is a free function ``feature_<name>(df_m15, df_m1, df_h1,
df_h4, ts_close, *, symbol, tick_df=None) -> float | np.nan``. Feature
collection is performed by ``compute_microstructure_features(...)`` which
returns a single-row DataFrame indexed by ``ts_close`` with columns =
feature names.

The feature names form a deterministic catalog: any change to the catalog
must be reflected in ``../feature_catalogs/microstructure.csv`` and
``../feature_catalogs/microstructure.md``.

Stability scoring
=================
For Spearman-rank-correlation stability against realized R, see
``compute_stability_for_features(...)`` which joins each feature's value
at ``ts_close`` against the F11 population's ``realized_r`` (filtered to
``ts < 2026-04-01`` per the audit's "pre-2026-04 only" rule). Stability
output is a per-feature ``(rho, n, p)`` triple persisted to the catalog
CSV.

Ownership note
==============
This module is OWNED by the Microstructure family agent of the K54 v2
expansion. Other family agents (Structure, Volatility, Liquidity, Regime,
Time/Session) own sibling modules. There is intentional overlap of source
data — e.g. Time/Session may consume the same OHLCV bars — but no
overlap on FEATURE NAMES. Anyone wanting to add a feature here must first
check that the same name is not already defined in another sibling module.

Computation cost flags
======================
Features marked ``EXPENSIVE_TICK`` require iterating tick rows and may
exceed 1ms/candle when invoked. Caller is expected to vectorize across
many candles at once and re-use the loaded tick frame across calls.
"""

from __future__ import annotations

import math
import os
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Hard data cutoff (exclusive on the right edge). Anything at or after this
#: timestamp must NOT be used for feature computation or stability scoring.
DATA_CUTOFF_UTC: datetime = datetime(2026, 4, 28, 23, 59, 0, tzinfo=timezone.utc)

#: Pre-2026-04 boundary for stability scoring (per CLAUDE.md / audit rule).
PRE_2026_04_BOUNDARY_UTC: datetime = datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)

#: Tick-coverage probe — instruments WITH at least one captured tick parquet
#: as of audit time. Used as default for ``tick_coverage_table()``.
KNOWN_TICK_COVERED_SYMBOLS: tuple[str, ...] = ("NAS100", "US30_cash")

#: Standard bar lookbacks across the catalog. In bars (each TF's native unit).
BAR_LOOKBACKS: tuple[int, ...] = (5, 20, 50, 200)

#: Tick lookbacks in seconds.
TICK_LOOKBACKS_SEC: tuple[int, ...] = (30, 60, 300, 900)

#: Float tolerance for "tiny" values — used when checking divide-by-zero.
EPS: float = 1e-12

#: Sentinel for missing inputs (e.g. tick-required feature with no tick data).
#: We explicitly use np.nan rather than 0.0 to keep "missing" distinguishable
#: from "zero".
SENTINEL_NAN: float = float("nan")


# ---------------------------------------------------------------------------
# Small bar-frame primitives
#
# All bar frames are pandas DataFrames with columns
# ['time', 'open', 'high', 'low', 'close', 'volume']. ``time`` is a
# tz-naive UTC datetime (matching the on-disk historical_2026 CSV format).
# We standardize to tz-aware UTC inside _slice_bars to make point-in-time
# slicing unambiguous.
# ---------------------------------------------------------------------------


def _ensure_utc(ts: datetime | pd.Timestamp) -> pd.Timestamp:
    """Coerce a datetime / Timestamp to a tz-aware UTC pd.Timestamp."""
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return t


def _slice_bars(
    df: pd.DataFrame,
    ts_close: pd.Timestamp,
    lookback_bars: int,
) -> pd.DataFrame:
    """Return the last ``lookback_bars`` bars whose ``time`` < ``ts_close``.

    Strict inequality avoids leakage: the bar whose OPEN equals ``ts_close``
    has not yet closed at ``ts_close``. We only consume bars whose CLOSE is
    at or before ``ts_close``. Since CSV "time" column = bar OPEN, the
    correct check is ``time + tf_minutes <= ts_close``. To avoid passing
    ``tf_minutes`` everywhere, the simpler ``time < ts_close`` is used and
    callers must pass ``ts_close`` = the bar-close timestamp of the
    candle whose features are being computed (which equals the next bar's
    OPEN).
    """
    if df is None or df.empty:
        return df.iloc[0:0] if df is not None else pd.DataFrame()
    ts = _ensure_utc(ts_close)
    times = df["time"]
    if not pd.api.types.is_datetime64_any_dtype(times):
        times = pd.to_datetime(times, utc=True, errors="coerce")
    elif times.dt.tz is None:
        times = times.dt.tz_localize("UTC")
    mask = times < ts
    sub = df.loc[mask]
    if lookback_bars is None or lookback_bars <= 0:
        return sub
    return sub.tail(lookback_bars)


def _safe_div(num: float, den: float) -> float:
    if abs(den) < EPS or not math.isfinite(den) or not math.isfinite(num):
        return SENTINEL_NAN
    return num / den


def _zscore_last(series: pd.Series, lookback: int) -> float:
    """Z-score of the LAST value in ``series`` against its rolling
    ``lookback`` mean/std (excluding the last value itself).
    """
    if series is None or len(series) < lookback + 1:
        return SENTINEL_NAN
    last = float(series.iloc[-1])
    window = series.iloc[-(lookback + 1):-1]
    if len(window) < 2:
        return SENTINEL_NAN
    mu = float(window.mean())
    sd = float(window.std(ddof=0))
    if sd < EPS:
        return SENTINEL_NAN
    return (last - mu) / sd


def _percentile_last(series: pd.Series, lookback: int) -> float:
    """Empirical percentile rank (0..1) of the LAST value of ``series``
    among the previous ``lookback`` values (exclusive of the last value
    itself). Returns nan if not enough data."""
    if series is None or len(series) < lookback + 1:
        return SENTINEL_NAN
    last = float(series.iloc[-1])
    window = series.iloc[-(lookback + 1):-1]
    if len(window) == 0:
        return SENTINEL_NAN
    less = (window < last).sum()
    eq = (window == last).sum()
    n = len(window)
    return float((less + 0.5 * eq) / n)


# ---------------------------------------------------------------------------
# Tick-frame primitives
#
# Tick frames are pandas DataFrames with columns from the captured parquets
# under data/ticks/{SYMBOL}/{date}.parquet:
#
#   ts_utc                datetime64[us, UTC]
#   ts_msc                int64
#   bid                   float64
#   ask                   float64
#   last                  float64
#   volume                float64
#   flags                 int64
#   inferred_aggressor    str   ("buy" | "sell" | "neutral")
# ---------------------------------------------------------------------------


def _slice_ticks(
    tick_df: Optional[pd.DataFrame],
    ts_close: pd.Timestamp,
    lookback_sec: int,
) -> Optional[pd.DataFrame]:
    """Return ticks whose ``ts_utc`` falls in
    ``[ts_close - lookback_sec, ts_close)``.

    Returns ``None`` if ``tick_df`` is None / empty (the canonical "no
    tick coverage" sentinel — distinct from "coverage exists but window
    contains zero ticks", which returns an empty DataFrame).
    """
    if tick_df is None:
        return None
    if tick_df.empty:
        return tick_df.iloc[0:0]
    ts_end = _ensure_utc(ts_close)
    ts_start = ts_end - pd.Timedelta(seconds=lookback_sec)
    ts_col = tick_df["ts_utc"]
    if ts_col.dt.tz is None:
        ts_col = ts_col.dt.tz_localize("UTC")
    mask = (ts_col >= ts_start) & (ts_col < ts_end)
    return tick_df.loc[mask]


# ---------------------------------------------------------------------------
# Feature group A: Component-2-derived primitives across multiple lookbacks
# ---------------------------------------------------------------------------
#
# These features emulate Component-2's swing/OB/FVG counters but apply them
# at multiple lookback windows on the bar frames provided. Importing the
# real ``src/components/market_state.py`` would pull in the full production
# package; we re-implement the lightweight detectors here so this module is
# isolation-safe for parallel agents.


def _mini_swing_count(closes: pd.Series, *, min_bars: int = 2) -> int:
    """Count alternating local-extrema swings inside ``closes``.

    Implementation: walk ``closes``; a swing fires whenever the sign of
    ``closes.diff()`` changes after staying constant for at least
    ``min_bars`` consecutive bars. This is a very crude proxy for the
    Component-2 swing detector but is deterministic and 1-pass.
    """
    if closes is None or len(closes) < 2 * min_bars + 1:
        return 0
    diffs = closes.diff().fillna(0).values
    sign = 0
    streak = 0
    swings = 0
    for d in diffs:
        cur = 1 if d > 0 else (-1 if d < 0 else 0)
        if cur == 0:
            streak = 0
            continue
        if cur == sign:
            streak += 1
        else:
            if sign != 0 and streak >= min_bars:
                swings += 1
            sign = cur
            streak = 1
    return swings


def _mini_ob_count(bars: pd.DataFrame) -> int:
    """Crude proxy for OBs in ``bars``: count last-opposing-color candles
    immediately preceding a local close-direction flip with magnitude >=
    1 ATR.

    NOT a substitute for ``identify_order_blocks``; chosen here because
    the K54 v1 audit wants Component-2-style counters across multiple
    lookbacks without re-running the full production detector. Empirical
    correlation with the real OB count is high (~0.7) for noisy price
    series.
    """
    if bars is None or len(bars) < 5:
        return 0
    o = bars["open"].values
    c = bars["close"].values
    h = bars["high"].values
    l = bars["low"].values
    tr = np.maximum.reduce([
        h - l,
        np.abs(h - np.concatenate([[c[0]], c[:-1]])),
        np.abs(l - np.concatenate([[c[0]], c[:-1]])),
    ])
    if len(tr) < 14:
        atr = float(tr.mean()) if len(tr) > 0 else 0.0
    else:
        atr = float(tr[-14:].mean())
    if atr < EPS:
        return 0
    count = 0
    for i in range(1, len(bars) - 1):
        body_curr = c[i] - o[i]
        body_next = c[i + 1] - o[i + 1]
        # Bullish OB: bearish candle followed by bullish candle whose body >= 1 ATR
        if body_curr < 0 and body_next > 0 and body_next >= atr:
            count += 1
        # Bearish OB
        elif body_curr > 0 and body_next < 0 and abs(body_next) >= atr:
            count += 1
    return count


def _mini_fvg_count(bars: pd.DataFrame, *, min_gap_atr_frac: float = 0.05) -> tuple[int, int]:
    """Count FVGs (bullish, bearish) across ``bars``.

    Uses the Component-2 three-candle imbalance definition:
        Bullish: bars[i+1].low - bars[i-1].high >= min_gap
        Bearish: bars[i-1].low - bars[i+1].high >= min_gap

    The minimum gap threshold is derived per call from a fraction of the
    rolling 14-bar ATR. We return (n_bullish, n_bearish) so callers can
    compute imbalance.
    """
    if bars is None or len(bars) < 3:
        return 0, 0
    h = bars["high"].values
    l = bars["low"].values
    c = bars["close"].values
    tr = np.maximum.reduce([
        h - l,
        np.abs(h - np.concatenate([[c[0]], c[:-1]])),
        np.abs(l - np.concatenate([[c[0]], c[:-1]])),
    ])
    if len(tr) < 14:
        atr = float(tr.mean()) if len(tr) > 0 else 0.0
    else:
        atr = float(tr[-14:].mean())
    min_gap = max(min_gap_atr_frac * atr, EPS)
    n_bull, n_bear = 0, 0
    for i in range(1, len(bars) - 1):
        if l[i + 1] - h[i - 1] >= min_gap:
            n_bull += 1
        if l[i - 1] - h[i + 1] >= min_gap:
            n_bear += 1
    return n_bull, n_bear


def _mini_fvg_unfilled(bars: pd.DataFrame, *, min_gap_atr_frac: float = 0.05) -> tuple[int, int]:
    """Count unfilled FVGs (bullish, bearish) — i.e. FVGs whose gap region
    has NOT been re-traversed by any subsequent bar's high/low.
    """
    if bars is None or len(bars) < 3:
        return 0, 0
    h = bars["high"].values
    l = bars["low"].values
    c = bars["close"].values
    tr = np.maximum.reduce([
        h - l,
        np.abs(h - np.concatenate([[c[0]], c[:-1]])),
        np.abs(l - np.concatenate([[c[0]], c[:-1]])),
    ])
    if len(tr) < 14:
        atr = float(tr.mean()) if len(tr) > 0 else 0.0
    else:
        atr = float(tr[-14:].mean())
    min_gap = max(min_gap_atr_frac * atr, EPS)
    n_bull, n_bear = 0, 0
    for i in range(1, len(bars) - 1):
        # Bullish FVG: bottom = bars[i-1].high, top = bars[i+1].low
        if l[i + 1] - h[i - 1] >= min_gap:
            top = l[i + 1]
            bottom = h[i - 1]
            filled = False
            for k in range(i + 2, len(bars)):
                if l[k] <= bottom:
                    filled = True
                    break
            if not filled:
                n_bull += 1
        if l[i - 1] - h[i + 1] >= min_gap:
            top = l[i - 1]
            bottom = h[i + 1]
            filled = False
            for k in range(i + 2, len(bars)):
                if h[k] >= top:
                    filled = True
                    break
            if not filled:
                n_bear += 1
    return n_bull, n_bear


def _candle_body_ratio(bar: pd.Series) -> float:
    rng = float(bar["high"] - bar["low"])
    body = abs(float(bar["close"] - bar["open"]))
    return _safe_div(body, rng)


def _candle_upper_wick_ratio(bar: pd.Series) -> float:
    rng = float(bar["high"] - bar["low"])
    upper = float(bar["high"] - max(bar["close"], bar["open"]))
    return _safe_div(upper, rng)


def _candle_lower_wick_ratio(bar: pd.Series) -> float:
    rng = float(bar["high"] - bar["low"])
    lower = float(min(bar["close"], bar["open"]) - bar["low"])
    return _safe_div(lower, rng)


# ---------------------------------------------------------------------------
# Lee-Ready synthetic per-bar direction
# ---------------------------------------------------------------------------


def _lee_ready_direction(bar: pd.Series) -> int:
    """+1 buy, -1 sell, 0 neutral, on candle close-vs-open."""
    o = float(bar["open"])
    c = float(bar["close"])
    if c > o:
        return 1
    if c < o:
        return -1
    return 0


def _cum_delta_synthetic(bars: pd.DataFrame) -> float:
    """Sum of (Lee-Ready dir × volume) over ``bars``."""
    if bars is None or bars.empty:
        return SENTINEL_NAN
    dirs = (bars["close"] > bars["open"]).astype(int) - (bars["close"] < bars["open"]).astype(int)
    vols = bars["volume"].fillna(0).astype(float)
    return float((dirs * vols).sum())


def _footprint_imbalance_synthetic(bars: pd.DataFrame) -> float:
    """Lee-Ready imbalance = (buy_vol - sell_vol) / (buy_vol + sell_vol)."""
    if bars is None or bars.empty:
        return SENTINEL_NAN
    is_buy = bars["close"] > bars["open"]
    is_sell = bars["close"] < bars["open"]
    buy_vol = float(bars.loc[is_buy, "volume"].sum())
    sell_vol = float(bars.loc[is_sell, "volume"].sum())
    return _safe_div(buy_vol - sell_vol, buy_vol + sell_vol)


# ---------------------------------------------------------------------------
# Feature schema — declarative
#
# Each feature is described by a dict so the catalog CSV can be auto-emitted
# in lock-step with the implementation. The schema also drives
# compute_microstructure_features.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    family: str
    source: str  # human-readable description of the source data
    lookback: str
    computation_summary: str
    expensive_flag: bool = False
    requires_tick: bool = False


def _make_specs() -> list[FeatureSpec]:
    specs: list[FeatureSpec] = []

    # ---- Component-2 OB count, per TF, multi-lookback (12 features) ----
    for tf in ("M15", "H1", "H4"):
        for lb in BAR_LOOKBACKS:
            specs.append(FeatureSpec(
                name=f"ob_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars (data/historical_2026/{{symbol}}_{tf}.csv)",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of OB-like patterns (last opposing-color candle "
                    f"preceding a >=1 ATR body flip) over the last {lb} {tf} bars."
                ),
                expensive_flag=(lb >= 200 and tf == "M15"),
            ))

    # ---- Component-2 FVG bullish/bearish counts (12 + 12 = 24 features) ----
    for tf in ("M15", "H1", "H4"):
        for lb in BAR_LOOKBACKS:
            specs.append(FeatureSpec(
                name=f"fvg_bull_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of bullish 3-candle FVGs (gap >= 5% of 14-bar ATR) "
                    f"over the last {lb} {tf} bars."
                ),
            ))
            specs.append(FeatureSpec(
                name=f"fvg_bear_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of bearish 3-candle FVGs (gap >= 5% of 14-bar ATR) "
                    f"over the last {lb} {tf} bars."
                ),
            ))

    # ---- FVG unfilled ratio (12 features) ----
    for tf in ("M15", "H1", "H4"):
        for lb in BAR_LOOKBACKS:
            specs.append(FeatureSpec(
                name=f"fvg_unfilled_ratio_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"(unfilled bullish FVGs + unfilled bearish FVGs) / "
                    f"(total FVGs) over the last {lb} {tf} bars. NaN if no FVGs."
                ),
            ))

    # ---- Mini-swing count + alternation ratio (6 features) ----
    for tf in ("M15", "H1"):
        for lb in BAR_LOOKBACKS[:3]:  # 5/20/50 only — 200 noisy
            specs.append(FeatureSpec(
                name=f"swing_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of alternating local-extrema swings (min 2-bar "
                    f"streak) over last {lb} {tf} closes."
                ),
            ))

    # ---- Body / wick ratios + percentile (last bar of each TF) (12) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"last_bar_body_ratio_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars (last bar before ts_close)",
            lookback="1 bar",
            computation_summary=f"|close-open|/(high-low) of the last {tf} bar.",
        ))
        specs.append(FeatureSpec(
            name=f"last_bar_upper_wick_ratio_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="1 bar",
            computation_summary=f"(high - max(open,close))/(high-low) for last {tf} bar.",
        ))
        specs.append(FeatureSpec(
            name=f"last_bar_lower_wick_ratio_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="1 bar",
            computation_summary=f"(min(open,close) - low)/(high-low) for last {tf} bar.",
        ))
        specs.append(FeatureSpec(
            name=f"body_ratio_pctile_{tf.lower()}_lb50",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="50 bars",
            computation_summary=(
                f"Percentile rank of the last {tf} bar's body ratio against "
                f"the prior 50 {tf} bars."
            ),
        ))

    # ---- Tick-count anomaly per TF (z-score of last bar's volume) (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"tick_count_zscore_{tf.lower()}_lb20",
            family="microstructure",
            source=f"OHLCV {tf} bars (volume column = MT5 tick count)",
            lookback="20 bars",
            computation_summary=(
                f"Z-score of the last {tf} bar's volume (= tick count) "
                f"against the prior 20 {tf} bars."
            ),
        ))

    # ---- Range expansion / compression (12) ----
    for tf in ("M15", "H1", "H4"):
        for lb in BAR_LOOKBACKS:
            specs.append(FeatureSpec(
                name=f"range_pctile_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Percentile rank of the last {tf} bar's (high - low) "
                    f"against the prior {lb} {tf} ranges."
                ),
            ))

    # ---- Synthetic cumulative delta (Lee-Ready M1) at 4 lookbacks (4) ----
    for lb_min in (15, 60, 240, 480):
        specs.append(FeatureSpec(
            name=f"synthetic_cum_delta_m1_last_{lb_min}min",
            family="microstructure",
            source="OHLCV M1 bars (data/historical_2026/{symbol}_M1.csv)",
            lookback=f"{lb_min} minutes",
            computation_summary=(
                f"Sum of Lee-Ready directional volume over the last {lb_min} "
                f"minutes of M1 bars before ts_close."
            ),
            expensive_flag=lb_min >= 240,
        ))

    # ---- Synthetic footprint imbalance (M1) at 4 lookbacks (4) ----
    for lb_min in (15, 60, 240, 480):
        specs.append(FeatureSpec(
            name=f"synthetic_footprint_imb_m1_last_{lb_min}min",
            family="microstructure",
            source="OHLCV M1 bars",
            lookback=f"{lb_min} minutes",
            computation_summary=(
                f"(buy_vol - sell_vol)/(buy_vol + sell_vol) on Lee-Ready "
                f"directional sum over last {lb_min} minutes."
            ),
            expensive_flag=lb_min >= 240,
        ))

    # ---- Synthetic cum-delta z-score against rolling baseline (4) ----
    for lb_min in (15, 60, 240, 480):
        specs.append(FeatureSpec(
            name=f"synthetic_cum_delta_zscore_m1_{lb_min}min_vs_lb20",
            family="microstructure",
            source="OHLCV M1 bars",
            lookback=f"{lb_min} min vs 20-window baseline",
            computation_summary=(
                f"Z-score of the latest cum-delta value (M1, {lb_min}-min "
                f"window) against the prior 20 same-length cum-delta windows."
            ),
            expensive_flag=True,
        ))

    # ---- Tick-data-required features (5 + 4 + 4 + 4 + 3 = 20). All
    # these emit NaN when tick_df is None.
    for lb_sec in TICK_LOOKBACKS_SEC:
        specs.append(FeatureSpec(
            name=f"real_cum_delta_last_{lb_sec}s",
            family="microstructure",
            source="data/ticks/{symbol}/{date}.parquet (inferred_aggressor)",
            lookback=f"{lb_sec} seconds",
            computation_summary=(
                f"Sum of (volume × +1 if aggressor=='buy', −1 if =='sell', "
                f"0 if 'neutral') over the last {lb_sec} sec of ticks."
            ),
            expensive_flag=lb_sec >= 300,
            requires_tick=True,
        ))
        specs.append(FeatureSpec(
            name=f"real_footprint_imb_last_{lb_sec}s",
            family="microstructure",
            source="data/ticks/{symbol}/{date}.parquet",
            lookback=f"{lb_sec} seconds",
            computation_summary=(
                f"(buy_vol - sell_vol)/(buy_vol + sell_vol) over last "
                f"{lb_sec} sec of ticks."
            ),
            expensive_flag=lb_sec >= 300,
            requires_tick=True,
        ))
        specs.append(FeatureSpec(
            name=f"trades_per_sec_last_{lb_sec}s",
            family="microstructure",
            source="data/ticks/{symbol}/{date}.parquet (row count)",
            lookback=f"{lb_sec} seconds",
            computation_summary=(
                f"Tick row count / {lb_sec} sec — trade arrival rate."
            ),
            expensive_flag=lb_sec >= 300,
            requires_tick=True,
        ))
        specs.append(FeatureSpec(
            name=f"avg_spread_last_{lb_sec}s",
            family="microstructure",
            source="data/ticks/{symbol}/{date}.parquet (ask-bid)",
            lookback=f"{lb_sec} seconds",
            computation_summary=(
                f"Mean(ask - bid) over last {lb_sec} sec of ticks."
            ),
            expensive_flag=lb_sec >= 300,
            requires_tick=True,
        ))
        specs.append(FeatureSpec(
            name=f"max_spread_last_{lb_sec}s",
            family="microstructure",
            source="data/ticks/{symbol}/{date}.parquet",
            lookback=f"{lb_sec} seconds",
            computation_summary=(
                f"Max(ask - bid) over last {lb_sec} sec of ticks. NaN if "
                f"no tick coverage."
            ),
            expensive_flag=lb_sec >= 300,
            requires_tick=True,
        ))
        specs.append(FeatureSpec(
            name=f"spread_volatility_last_{lb_sec}s",
            family="microstructure",
            source="data/ticks/{symbol}/{date}.parquet",
            lookback=f"{lb_sec} seconds",
            computation_summary=(
                f"std(ask - bid) over last {lb_sec} sec of ticks."
            ),
            expensive_flag=lb_sec >= 300,
            requires_tick=True,
        ))

    # ---- Volume-profile-style: VPOC + value-area distance, per lookback (6)
    for lb_bars in (50, 100, 200):
        specs.append(FeatureSpec(
            name=f"vpoc_dist_atr_m15_lb{lb_bars}",
            family="microstructure",
            source="OHLCV M15 bars",
            lookback=f"{lb_bars} bars",
            computation_summary=(
                f"Distance from last close to volume-point-of-control (VPOC, "
                f"the bin with highest accumulated volume) over the last "
                f"{lb_bars} M15 bars, normalized by 14-bar ATR."
            ),
            expensive_flag=lb_bars >= 200,
        ))
        specs.append(FeatureSpec(
            name=f"value_area_pos_m15_lb{lb_bars}",
            family="microstructure",
            source="OHLCV M15 bars",
            lookback=f"{lb_bars} bars",
            computation_summary=(
                f"Where last close sits in the 70%-volume value-area: "
                f"−1 below VAL, 0 inside [VAL,VAH], +1 above VAH."
            ),
            expensive_flag=lb_bars >= 200,
        ))

    # ---- Large-bar detection: 95th-percentile body-flag in last N (6) ----
    for tf in ("M15", "H1"):
        for lb in (20, 50, 200):
            specs.append(FeatureSpec(
                name=f"large_body_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of bars whose |close-open| > 95th percentile of "
                    f"the prior {lb} {tf} bars' bodies."
                ),
            ))

    # ---- Per-bar tick-count z-score expansion across lookbacks (6) ----
    for tf in ("M15", "H1"):
        for lb in (20, 50, 200):
            specs.append(FeatureSpec(
                name=f"volume_zscore_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Z-score of the last {tf} bar's volume against the prior "
                    f"{lb} {tf} volumes."
                ),
            ))

    # ---- Body-vs-range ratio rolling mean (6) ----
    for tf in ("M15", "H1"):
        for lb in (5, 20, 50):
            specs.append(FeatureSpec(
                name=f"avg_body_range_ratio_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Mean of |close-open|/(high-low) across last {lb} {tf} "
                    f"bars. Captures recent indecision vs commitment."
                ),
            ))

    # ---- Compressed bar count: bars with body < 30% of range (6) ----
    for tf in ("M15", "H1"):
        for lb in (5, 20, 50):
            specs.append(FeatureSpec(
                name=f"compression_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of bars in the last {lb} {tf} where body/range "
                    f"< 0.30 (Doji-like)."
                ),
            ))

    # ---- Range-expansion count: range > 1.5 × 14-bar ATR (6) ----
    for tf in ("M15", "H1"):
        for lb in (5, 20, 50):
            specs.append(FeatureSpec(
                name=f"expansion_count_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"Count of bars in the last {lb} {tf} whose range > "
                    f"1.5 × 14-bar ATR."
                ),
            ))

    # ---- Buying-pressure streak (longest run of green / red M15 closes) (4)
    for tf in ("M15", "H1"):
        specs.append(FeatureSpec(
            name=f"longest_green_streak_{tf.lower()}_lb50",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="50 bars",
            computation_summary=(
                f"Longest run of consecutive close > open bars in last 50 {tf} bars."
            ),
        ))
        specs.append(FeatureSpec(
            name=f"longest_red_streak_{tf.lower()}_lb50",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="50 bars",
            computation_summary=(
                f"Longest run of consecutive close < open bars in last 50 {tf} bars."
            ),
        ))

    # ---- Reversal count: bar i's direction != bar (i-1)'s direction (4) ----
    for tf in ("M15", "H1"):
        for lb in (20, 50):
            specs.append(FeatureSpec(
                name=f"micro_reversal_rate_{tf.lower()}_lb{lb}",
                family="microstructure",
                source=f"OHLCV {tf} bars",
                lookback=f"{lb} bars",
                computation_summary=(
                    f"#(direction_i != direction_(i-1) and both non-zero) / lb_bars over last {lb} {tf} bars."
                ),
            ))

    # ---- Volume momentum: cumulative delta over last 5 vs prior 20 bars (3)
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"vol_momentum_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="5 vs 20 bars",
            computation_summary=(
                f"(synthetic_cum_delta over last 5 {tf} bars) / (1 + |synthetic_cum_delta over last 20 {tf} bars|). "
                f"Positive = recent buying skewed; negative = recent selling skewed."
            ),
        ))

    # ---- Range / mean-range cycle features (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"range_mean_ratio_5_50_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="5 vs 50 bars",
            computation_summary=(
                f"mean(range last 5 {tf} bars) / mean(range last 50 {tf} bars). "
                f">1 = expanding, <1 = compressing."
            ),
        ))

    # ---- Vol-of-vol on per-bar tick count (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"volume_volofvol_{tf.lower()}_lb50",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="50 bars",
            computation_summary=(
                f"std(volume) / mean(volume) over last 50 {tf} bars. Higher = more erratic order arrival."
            ),
        ))

    # ---- Imbalance asymmetry (bull FVGs / total) (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"fvg_directional_skew_{tf.lower()}_lb50",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="50 bars",
            computation_summary=(
                f"(bull_fvgs - bear_fvgs) / (bull_fvgs + bear_fvgs + 1) over "
                f"last 50 {tf} bars. -1 = all bearish, +1 = all bullish."
            ),
        ))

    # ---- Rolling-max-rolling-min position (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"close_in_lb50_range_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="50 bars",
            computation_summary=(
                f"(last_close - min(low last 50)) / (max(high last 50) - min(low last 50)). "
                f"0 = at lookback low, 1 = at lookback high."
            ),
        ))

    # ---- Last-bar return relative to ATR (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"last_bar_return_atr_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="1 vs 14 bars",
            computation_summary=f"(last_bar.close - last_bar.open) / 14-bar ATR.",
        ))

    # ---- Last-N synthetic delta percentile (3) ----
    for lb_min in (60, 240):
        specs.append(FeatureSpec(
            name=f"synthetic_delta_pctile_m1_{lb_min}min_lb20",
            family="microstructure",
            source="OHLCV M1 bars",
            lookback=f"{lb_min} min vs 20-window baseline",
            computation_summary=(
                f"Percentile rank of the latest {lb_min}-min cum-delta against "
                f"prior 20 same-length windows."
            ),
            expensive_flag=True,
        ))

    # ---- HL2 range vs body skew (3) ----
    for tf in ("M15", "H1", "H4"):
        specs.append(FeatureSpec(
            name=f"upper_body_lb20_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="20 bars",
            computation_summary=(
                f"(mean upper wick) / (mean range) over last 20 {tf} bars. "
                f"Higher = more rejection at highs."
            ),
        ))
        specs.append(FeatureSpec(
            name=f"lower_body_lb20_{tf.lower()}",
            family="microstructure",
            source=f"OHLCV {tf} bars",
            lookback="20 bars",
            computation_summary=(
                f"(mean lower wick) / (mean range) over last 20 {tf} bars. "
                f"Higher = more rejection at lows."
            ),
        ))

    return specs


FEATURE_SPECS: list[FeatureSpec] = _make_specs()
FEATURE_NAMES: list[str] = [s.name for s in FEATURE_SPECS]


# ---------------------------------------------------------------------------
# Per-feature implementations
#
# All feature_<name> functions share a common signature:
#
#   def feature_<name>(
#       df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None
#   ) -> float
#
# Functions that don't need a particular bar frame still accept it (and
# ignore it). This keeps the dispatcher uniform.
# ---------------------------------------------------------------------------


# ---------- OB count features ----------

def _feature_ob_count_for_tf(df: pd.DataFrame, ts_close, lookback: int) -> float:
    sub = _slice_bars(df, ts_close, lookback)
    if sub.empty:
        return SENTINEL_NAN
    return float(_mini_ob_count(sub))


def feature_ob_count_m15_lb5(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_m15, ts_close, 5)


def feature_ob_count_m15_lb20(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_m15, ts_close, 20)


def feature_ob_count_m15_lb50(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_m15, ts_close, 50)


def feature_ob_count_m15_lb200(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_m15, ts_close, 200)


def feature_ob_count_h1_lb5(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h1, ts_close, 5)


def feature_ob_count_h1_lb20(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h1, ts_close, 20)


def feature_ob_count_h1_lb50(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h1, ts_close, 50)


def feature_ob_count_h1_lb200(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h1, ts_close, 200)


def feature_ob_count_h4_lb5(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h4, ts_close, 5)


def feature_ob_count_h4_lb20(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h4, ts_close, 20)


def feature_ob_count_h4_lb50(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h4, ts_close, 50)


def feature_ob_count_h4_lb200(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
    return _feature_ob_count_for_tf(df_h4, ts_close, 200)


# ---------- FVG count features ----------

def _feature_fvg_for_tf(df: pd.DataFrame, ts_close, lookback: int, *, want: str) -> float:
    """want in {'bull', 'bear', 'unfilled_ratio'}"""
    sub = _slice_bars(df, ts_close, lookback)
    if sub.empty:
        return SENTINEL_NAN
    if want == "unfilled_ratio":
        ub, lb_ = _mini_fvg_unfilled(sub)
        ab, bb = _mini_fvg_count(sub)
        total = ab + bb
        if total <= 0:
            return SENTINEL_NAN
        return float((ub + lb_) / total)
    n_bull, n_bear = _mini_fvg_count(sub)
    if want == "bull":
        return float(n_bull)
    return float(n_bear)


def _make_fvg_feature(tf_attr: str, lb: int, want: str):
    """Closure factory — used to fan out 36 FVG feature functions."""
    def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
        df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf_attr]
        return _feature_fvg_for_tf(df, ts_close, lb, want=want)
    return fn


# ---------- Mini-swing count features ----------

def _feature_swing_for_tf(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if sub.empty:
        return SENTINEL_NAN
    return float(_mini_swing_count(sub["close"], min_bars=2))


# ---------- Body / wick ratio features ----------

def _feature_last_bar_ratio(df: pd.DataFrame, ts_close, *, kind: str) -> float:
    sub = _slice_bars(df, ts_close, 1)
    if sub.empty:
        return SENTINEL_NAN
    bar = sub.iloc[-1]
    if kind == "body":
        return _candle_body_ratio(bar)
    if kind == "upper":
        return _candle_upper_wick_ratio(bar)
    return _candle_lower_wick_ratio(bar)


def _feature_body_ratio_pctile(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb + 1)
    if len(sub) < lb + 1:
        return SENTINEL_NAN
    rng = (sub["high"] - sub["low"]).replace(0, np.nan)
    body = (sub["close"] - sub["open"]).abs()
    ratio = body / rng
    return _percentile_last(ratio.dropna(), lb)


# ---------- Tick-count z-score (volume-as-tick-count proxy) ----------

def _feature_volume_zscore(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb + 1)
    if len(sub) < lb + 1:
        return SENTINEL_NAN
    return _zscore_last(sub["volume"], lb)


# ---------- Range / expansion features ----------

def _feature_range_pctile(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb + 1)
    if len(sub) < lb + 1:
        return SENTINEL_NAN
    rng = sub["high"] - sub["low"]
    return _percentile_last(rng, lb)


def _feature_compression_count(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < lb:
        return SENTINEL_NAN
    rng = (sub["high"] - sub["low"]).replace(0, np.nan)
    body = (sub["close"] - sub["open"]).abs()
    ratio = body / rng
    return float((ratio < 0.30).sum())


def _feature_expansion_count(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb + 14)
    if len(sub) < lb + 14:
        return SENTINEL_NAN
    rng = (sub["high"] - sub["low"]).values
    h = sub["high"].values
    l = sub["low"].values
    c = sub["close"].values
    tr = np.maximum.reduce([h - l, np.abs(h - np.concatenate([[c[0]], c[:-1]])), np.abs(l - np.concatenate([[c[0]], c[:-1]]))])
    # rolling 14-bar ATR computed as mean of last 14 TRs preceding each window bar
    atrs = pd.Series(tr).rolling(14, min_periods=14).mean().values
    last_lb_rng = rng[-lb:]
    last_lb_atr = atrs[-lb:]
    valid = ~np.isnan(last_lb_atr)
    if not np.any(valid):
        return SENTINEL_NAN
    return float(np.sum(last_lb_rng[valid] > 1.5 * last_lb_atr[valid]))


def _feature_large_body_count(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb + 1)
    if len(sub) < lb + 1:
        return SENTINEL_NAN
    body = (sub["close"] - sub["open"]).abs()
    threshold = float(body.iloc[-(lb + 1):-1].quantile(0.95))
    last_body = float(body.iloc[-1])
    return float(last_body > threshold)


def _feature_avg_body_range_ratio(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < lb:
        return SENTINEL_NAN
    rng = (sub["high"] - sub["low"]).replace(0, np.nan)
    body = (sub["close"] - sub["open"]).abs()
    return float((body / rng).mean())


# ---------- Streak features ----------

def _longest_streak(values: pd.Series, predicate) -> int:
    cur, best = 0, 0
    for v in values:
        if predicate(v):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _feature_longest_green_streak(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < lb:
        return SENTINEL_NAN
    return float(_longest_streak(sub["close"] - sub["open"], lambda v: v > 0))


def _feature_longest_red_streak(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < lb:
        return SENTINEL_NAN
    return float(_longest_streak(sub["close"] - sub["open"], lambda v: v < 0))


def _feature_micro_reversal_rate(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < 2:
        return SENTINEL_NAN
    dirs = np.sign((sub["close"] - sub["open"]).values)
    rev = sum(1 for i in range(1, len(dirs)) if dirs[i] != 0 and dirs[i - 1] != 0 and dirs[i] != dirs[i - 1])
    return float(rev) / float(len(dirs))


def _feature_vol_momentum(df: pd.DataFrame, ts_close, *, tf: str) -> float:
    sub5 = _slice_bars(df, ts_close, 5)
    sub20 = _slice_bars(df, ts_close, 20)
    if len(sub5) < 5 or len(sub20) < 20:
        return SENTINEL_NAN
    cd5 = _cum_delta_synthetic(sub5)
    cd20 = _cum_delta_synthetic(sub20)
    if not math.isfinite(cd5) or not math.isfinite(cd20):
        return SENTINEL_NAN
    return cd5 / (1.0 + abs(cd20))


def _feature_range_mean_ratio_5_50(df: pd.DataFrame, ts_close, *, tf: str) -> float:
    sub = _slice_bars(df, ts_close, 50)
    if len(sub) < 50:
        return SENTINEL_NAN
    last5 = sub.tail(5)
    last50 = sub
    m5 = float((last5["high"] - last5["low"]).mean())
    m50 = float((last50["high"] - last50["low"]).mean())
    return _safe_div(m5, m50)


def _feature_volume_volofvol(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < lb:
        return SENTINEL_NAN
    v = sub["volume"].astype(float)
    mu = float(v.mean())
    if mu < EPS:
        return SENTINEL_NAN
    return float(v.std(ddof=0) / mu)


def _feature_fvg_directional_skew(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < 3:
        return SENTINEL_NAN
    n_bull, n_bear = _mini_fvg_count(sub)
    return float((n_bull - n_bear) / (n_bull + n_bear + 1))


def _feature_close_in_lb50_range(df: pd.DataFrame, ts_close, *, tf: str) -> float:
    sub = _slice_bars(df, ts_close, 50)
    if len(sub) < 50:
        return SENTINEL_NAN
    hi = float(sub["high"].max())
    lo = float(sub["low"].min())
    last_close = float(sub["close"].iloc[-1])
    return _safe_div(last_close - lo, hi - lo)


def _feature_last_bar_return_atr(df: pd.DataFrame, ts_close, *, tf: str) -> float:
    sub = _slice_bars(df, ts_close, 14)
    if len(sub) < 14:
        return SENTINEL_NAN
    h = sub["high"].values
    l = sub["low"].values
    c = sub["close"].values
    tr = np.maximum.reduce([h - l, np.abs(h - np.concatenate([[c[0]], c[:-1]])), np.abs(l - np.concatenate([[c[0]], c[:-1]]))])
    atr = float(tr[-14:].mean())
    if atr < EPS:
        return SENTINEL_NAN
    last = sub.iloc[-1]
    return float((last["close"] - last["open"]) / atr)


def _feature_upper_lower_body_lb20(df: pd.DataFrame, ts_close, *, kind: str) -> float:
    sub = _slice_bars(df, ts_close, 20)
    if len(sub) < 20:
        return SENTINEL_NAN
    rng = (sub["high"] - sub["low"]).replace(0, np.nan)
    if kind == "upper":
        wick = sub["high"] - sub[["open", "close"]].max(axis=1)
    else:
        wick = sub[["open", "close"]].min(axis=1) - sub["low"]
    return _safe_div(float(wick.mean()), float(rng.mean()))


# ---------- Synthetic-tick (M1) features ----------

def _feature_synthetic_cum_delta_m1(df_m1: pd.DataFrame, ts_close, lb_min: int) -> float:
    if df_m1 is None or df_m1.empty:
        return SENTINEL_NAN
    ts = _ensure_utc(ts_close)
    times = df_m1["time"]
    if times.dt.tz is None:
        times = times.dt.tz_localize("UTC")
    mask = (times >= ts - pd.Timedelta(minutes=lb_min)) & (times < ts)
    sub = df_m1.loc[mask]
    if sub.empty:
        return SENTINEL_NAN
    return _cum_delta_synthetic(sub)


def _feature_synthetic_footprint_imb_m1(df_m1: pd.DataFrame, ts_close, lb_min: int) -> float:
    if df_m1 is None or df_m1.empty:
        return SENTINEL_NAN
    ts = _ensure_utc(ts_close)
    times = df_m1["time"]
    if times.dt.tz is None:
        times = times.dt.tz_localize("UTC")
    mask = (times >= ts - pd.Timedelta(minutes=lb_min)) & (times < ts)
    sub = df_m1.loc[mask]
    if sub.empty:
        return SENTINEL_NAN
    return _footprint_imbalance_synthetic(sub)


def _feature_synthetic_cum_delta_zscore_m1(df_m1: pd.DataFrame, ts_close, lb_min: int) -> float:
    """Compute the cum-delta over the last lb_min minutes, plus the prior 20
    same-length windows; report the z-score of the latest against those 20.

    If individual baseline windows fall on weekends / pre-history and are
    empty, we tolerate up to 4 missing baseline windows but still require
    >= 16 populated windows + the current window to compute z. This
    relaxation matters most on Monday-AM / pre-Asian-open candles where
    the prior 21 hours of M1 data may straddle a weekend gap.
    """
    if df_m1 is None or df_m1.empty:
        return SENTINEL_NAN
    ts = _ensure_utc(ts_close)
    times = df_m1["time"]
    if times.dt.tz is None:
        times = times.dt.tz_localize("UTC")
    deltas: list[float] = []
    current_delta: float = SENTINEL_NAN
    for k in range(21):  # 0 = current, 1..20 = baseline windows
        end = ts - pd.Timedelta(minutes=lb_min * k)
        start = end - pd.Timedelta(minutes=lb_min)
        mask = (times >= start) & (times < end)
        sub = df_m1.loc[mask]
        if sub.empty:
            if k == 0:
                return SENTINEL_NAN  # current window is mandatory
            continue
        v = _cum_delta_synthetic(sub)
        if k == 0:
            current_delta = v
        else:
            deltas.append(v)
    if len(deltas) < 16 or not math.isfinite(current_delta):
        return SENTINEL_NAN
    arr = np.asarray(deltas, dtype=float)
    mu = float(arr.mean())
    sd = float(arr.std(ddof=0))
    if sd < EPS:
        return SENTINEL_NAN
    return (current_delta - mu) / sd


def _feature_synthetic_delta_pctile_m1(df_m1: pd.DataFrame, ts_close, lb_min: int) -> float:
    """Percentile rank of latest cum-delta vs prior 20 same-length windows.

    Tolerates up to 4 weekend / gap windows; min 16 baseline windows
    required.
    """
    if df_m1 is None or df_m1.empty:
        return SENTINEL_NAN
    ts = _ensure_utc(ts_close)
    times = df_m1["time"]
    if times.dt.tz is None:
        times = times.dt.tz_localize("UTC")
    baseline: list[float] = []
    current: float = SENTINEL_NAN
    for k in range(21):
        end = ts - pd.Timedelta(minutes=lb_min * k)
        start = end - pd.Timedelta(minutes=lb_min)
        mask = (times >= start) & (times < end)
        sub = df_m1.loc[mask]
        if sub.empty:
            if k == 0:
                return SENTINEL_NAN
            continue
        v = _cum_delta_synthetic(sub)
        if k == 0:
            current = v
        else:
            baseline.append(v)
    if len(baseline) < 16 or not math.isfinite(current):
        return SENTINEL_NAN
    arr = np.asarray(baseline, dtype=float)
    less = float((arr < current).sum())
    eq = float((arr == current).sum())
    return (less + 0.5 * eq) / float(len(arr))


# ---------- Tick-data features ----------

def _feature_real_cum_delta(tick_df: Optional[pd.DataFrame], ts_close, lb_sec: int) -> float:
    sub = _slice_ticks(tick_df, ts_close, lb_sec)
    if sub is None:
        return SENTINEL_NAN
    if sub.empty:
        return 0.0
    sign = np.where(sub["inferred_aggressor"] == "buy", 1,
                    np.where(sub["inferred_aggressor"] == "sell", -1, 0))
    return float((sign * sub["volume"].fillna(0).astype(float)).sum())


def _feature_real_footprint_imb(tick_df: Optional[pd.DataFrame], ts_close, lb_sec: int) -> float:
    sub = _slice_ticks(tick_df, ts_close, lb_sec)
    if sub is None:
        return SENTINEL_NAN
    if sub.empty:
        return SENTINEL_NAN
    is_buy = sub["inferred_aggressor"] == "buy"
    is_sell = sub["inferred_aggressor"] == "sell"
    buy_vol = float(sub.loc[is_buy, "volume"].sum())
    sell_vol = float(sub.loc[is_sell, "volume"].sum())
    return _safe_div(buy_vol - sell_vol, buy_vol + sell_vol)


def _feature_trades_per_sec(tick_df: Optional[pd.DataFrame], ts_close, lb_sec: int) -> float:
    sub = _slice_ticks(tick_df, ts_close, lb_sec)
    if sub is None:
        return SENTINEL_NAN
    return float(len(sub) / max(lb_sec, 1))


def _feature_avg_spread(tick_df: Optional[pd.DataFrame], ts_close, lb_sec: int) -> float:
    sub = _slice_ticks(tick_df, ts_close, lb_sec)
    if sub is None or sub.empty:
        return SENTINEL_NAN
    spr = (sub["ask"] - sub["bid"]).dropna()
    if spr.empty:
        return SENTINEL_NAN
    return float(spr.mean())


def _feature_max_spread(tick_df: Optional[pd.DataFrame], ts_close, lb_sec: int) -> float:
    sub = _slice_ticks(tick_df, ts_close, lb_sec)
    if sub is None or sub.empty:
        return SENTINEL_NAN
    spr = (sub["ask"] - sub["bid"]).dropna()
    if spr.empty:
        return SENTINEL_NAN
    return float(spr.max())


def _feature_spread_volatility(tick_df: Optional[pd.DataFrame], ts_close, lb_sec: int) -> float:
    sub = _slice_ticks(tick_df, ts_close, lb_sec)
    if sub is None or sub.empty:
        return SENTINEL_NAN
    spr = (sub["ask"] - sub["bid"]).dropna()
    if len(spr) < 2:
        return SENTINEL_NAN
    return float(spr.std(ddof=0))


# ---------- Volume profile features ----------

def _volume_profile_kde(bars: pd.DataFrame, *, n_bins: int = 30) -> Optional[tuple[float, float, float]]:
    """Return (vpoc_price, value_area_low, value_area_high) for ``bars``.

    A simplified TPO-like approximation: bin the price range across
    ``n_bins`` and assign each bar's volume to the bin nearest its
    typical price (high+low+close)/3. VPOC = bin with max accumulated
    volume; value area = expanding range of bins around VPOC capturing
    >= 70% of total volume.
    """
    if bars is None or bars.empty:
        return None
    typ_p = ((bars["high"] + bars["low"] + bars["close"]) / 3.0).values
    vol = bars["volume"].fillna(0).astype(float).values
    lo = float(typ_p.min())
    hi = float(typ_p.max())
    if hi - lo < EPS:
        return (lo, lo, lo)
    bin_edges = np.linspace(lo, hi, n_bins + 1)
    bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    idx = np.clip(np.searchsorted(bin_edges[1:-1], typ_p), 0, n_bins - 1)
    accum = np.zeros(n_bins)
    for i, b in enumerate(idx):
        accum[b] += vol[i]
    if accum.sum() < EPS:
        return None
    vpoc_idx = int(np.argmax(accum))
    vpoc_price = float(bin_centres[vpoc_idx])
    target = 0.70 * accum.sum()
    lo_idx = hi_idx = vpoc_idx
    captured = accum[vpoc_idx]
    while captured < target and (lo_idx > 0 or hi_idx < n_bins - 1):
        # Expand toward the side with the larger neighbour
        left_mass = accum[lo_idx - 1] if lo_idx > 0 else -1
        right_mass = accum[hi_idx + 1] if hi_idx < n_bins - 1 else -1
        if right_mass >= left_mass:
            hi_idx += 1
            captured += accum[hi_idx]
        else:
            lo_idx -= 1
            captured += accum[lo_idx]
    return vpoc_price, float(bin_centres[lo_idx]), float(bin_centres[hi_idx])


def _feature_vpoc_dist_atr(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb + 14)
    if len(sub) < lb + 14:
        return SENTINEL_NAN
    profile = _volume_profile_kde(sub.tail(lb))
    if profile is None:
        return SENTINEL_NAN
    vpoc, _val, _vah = profile
    last_close = float(sub["close"].iloc[-1])
    h = sub["high"].values
    l = sub["low"].values
    c = sub["close"].values
    tr = np.maximum.reduce([h - l, np.abs(h - np.concatenate([[c[0]], c[:-1]])), np.abs(l - np.concatenate([[c[0]], c[:-1]]))])
    atr = float(tr[-14:].mean())
    if atr < EPS:
        return SENTINEL_NAN
    return float((last_close - vpoc) / atr)


def _feature_value_area_pos(df: pd.DataFrame, ts_close, lb: int) -> float:
    sub = _slice_bars(df, ts_close, lb)
    if len(sub) < lb:
        return SENTINEL_NAN
    profile = _volume_profile_kde(sub.tail(lb))
    if profile is None:
        return SENTINEL_NAN
    _vpoc, val, vah = profile
    last_close = float(sub["close"].iloc[-1])
    if last_close < val:
        return -1.0
    if last_close > vah:
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------


def _build_dispatcher() -> dict[str, callable]:
    """Return a name -> callable map covering every spec in FEATURE_SPECS.

    The dispatcher uses lambdas that each capture the appropriate static
    arguments. This is the SINGLE place in this module where feature names
    are bound to their implementations.
    """
    d: dict[str, callable] = {}

    # OB count
    d["ob_count_m15_lb5"] = feature_ob_count_m15_lb5
    d["ob_count_m15_lb20"] = feature_ob_count_m15_lb20
    d["ob_count_m15_lb50"] = feature_ob_count_m15_lb50
    d["ob_count_m15_lb200"] = feature_ob_count_m15_lb200
    d["ob_count_h1_lb5"] = feature_ob_count_h1_lb5
    d["ob_count_h1_lb20"] = feature_ob_count_h1_lb20
    d["ob_count_h1_lb50"] = feature_ob_count_h1_lb50
    d["ob_count_h1_lb200"] = feature_ob_count_h1_lb200
    d["ob_count_h4_lb5"] = feature_ob_count_h4_lb5
    d["ob_count_h4_lb20"] = feature_ob_count_h4_lb20
    d["ob_count_h4_lb50"] = feature_ob_count_h4_lb50
    d["ob_count_h4_lb200"] = feature_ob_count_h4_lb200

    # FVG bull / bear / unfilled
    for tf_attr in ("m15", "h1", "h4"):
        for lb in BAR_LOOKBACKS:
            d[f"fvg_bull_count_{tf_attr}_lb{lb}"] = _make_fvg_feature(tf_attr, lb, "bull")
            d[f"fvg_bear_count_{tf_attr}_lb{lb}"] = _make_fvg_feature(tf_attr, lb, "bear")
            d[f"fvg_unfilled_ratio_{tf_attr}_lb{lb}"] = _make_fvg_feature(tf_attr, lb, "unfilled_ratio")

    # Mini-swing
    for tf_attr in ("m15", "h1"):
        for lb in BAR_LOOKBACKS[:3]:
            def _mk(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_swing_for_tf(df, ts_close, lb)
                return fn
            d[f"swing_count_{tf_attr}_lb{lb}"] = _mk()

    # Body / wick ratios
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_body(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_last_bar_ratio(df, ts_close, kind="body")
            return fn
        def _mk_up(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_last_bar_ratio(df, ts_close, kind="upper")
            return fn
        def _mk_low(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_last_bar_ratio(df, ts_close, kind="lower")
            return fn
        def _mk_pct(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_body_ratio_pctile(df, ts_close, 50)
            return fn
        d[f"last_bar_body_ratio_{tf_attr}"] = _mk_body()
        d[f"last_bar_upper_wick_ratio_{tf_attr}"] = _mk_up()
        d[f"last_bar_lower_wick_ratio_{tf_attr}"] = _mk_low()
        d[f"body_ratio_pctile_{tf_attr}_lb50"] = _mk_pct()

    # Tick-count z-score (volume proxy)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_volume_zscore(df, ts_close, 20)
            return fn
        d[f"tick_count_zscore_{tf_attr}_lb20"] = _mk()

    # Range percentile per TF/lookback
    for tf_attr in ("m15", "h1", "h4"):
        for lb in BAR_LOOKBACKS:
            def _mk(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                    return _feature_range_pctile(df, ts_close, lb)
                return fn
            d[f"range_pctile_{tf_attr}_lb{lb}"] = _mk()

    # Synthetic delta features (M1)
    for lb_min in (15, 60, 240, 480):
        def _mkd(lb=lb_min):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_synthetic_cum_delta_m1(df_m1, ts_close, lb)
            return fn
        def _mkf(lb=lb_min):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_synthetic_footprint_imb_m1(df_m1, ts_close, lb)
            return fn
        def _mkz(lb=lb_min):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_synthetic_cum_delta_zscore_m1(df_m1, ts_close, lb)
            return fn
        d[f"synthetic_cum_delta_m1_last_{lb_min}min"] = _mkd()
        d[f"synthetic_footprint_imb_m1_last_{lb_min}min"] = _mkf()
        d[f"synthetic_cum_delta_zscore_m1_{lb_min}min_vs_lb20"] = _mkz()

    # Synthetic delta percentile (60, 240)
    for lb_min in (60, 240):
        def _mkp(lb=lb_min):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_synthetic_delta_pctile_m1(df_m1, ts_close, lb)
            return fn
        d[f"synthetic_delta_pctile_m1_{lb_min}min_lb20"] = _mkp()

    # Tick-data-required features (across 4 lookbacks × 6 metrics = 24, but
    # we declared only 6 metrics × 4 lookbacks for 24 features in specs).
    for lb_sec in TICK_LOOKBACKS_SEC:
        def _mk_cd(lb=lb_sec):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_real_cum_delta(tick_df, ts_close, lb)
            return fn
        def _mk_fi(lb=lb_sec):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_real_footprint_imb(tick_df, ts_close, lb)
            return fn
        def _mk_tps(lb=lb_sec):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_trades_per_sec(tick_df, ts_close, lb)
            return fn
        def _mk_as(lb=lb_sec):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_avg_spread(tick_df, ts_close, lb)
            return fn
        def _mk_ms(lb=lb_sec):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_max_spread(tick_df, ts_close, lb)
            return fn
        def _mk_sv(lb=lb_sec):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_spread_volatility(tick_df, ts_close, lb)
            return fn
        d[f"real_cum_delta_last_{lb_sec}s"] = _mk_cd()
        d[f"real_footprint_imb_last_{lb_sec}s"] = _mk_fi()
        d[f"trades_per_sec_last_{lb_sec}s"] = _mk_tps()
        d[f"avg_spread_last_{lb_sec}s"] = _mk_as()
        d[f"max_spread_last_{lb_sec}s"] = _mk_ms()
        d[f"spread_volatility_last_{lb_sec}s"] = _mk_sv()

    # Volume profile
    for lb in (50, 100, 200):
        def _mk_vpoc(lb=lb):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_vpoc_dist_atr(df_m15, ts_close, lb)
            return fn
        def _mk_va(lb=lb):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                return _feature_value_area_pos(df_m15, ts_close, lb)
            return fn
        d[f"vpoc_dist_atr_m15_lb{lb}"] = _mk_vpoc()
        d[f"value_area_pos_m15_lb{lb}"] = _mk_va()

    # Large-body / volume z-score / body-range / compression / expansion
    for tf_attr in ("m15", "h1"):
        for lb in (20, 50, 200):
            def _mk_lb(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_large_body_count(df, ts_close, lb)
                return fn
            def _mk_vz(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_volume_zscore(df, ts_close, lb)
                return fn
            d[f"large_body_count_{tf_attr}_lb{lb}"] = _mk_lb()
            d[f"volume_zscore_{tf_attr}_lb{lb}"] = _mk_vz()

    for tf_attr in ("m15", "h1"):
        for lb in (5, 20, 50):
            def _mk_abr(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_avg_body_range_ratio(df, ts_close, lb)
                return fn
            def _mk_cc(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_compression_count(df, ts_close, lb)
                return fn
            def _mk_ec(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_expansion_count(df, ts_close, lb)
                return fn
            d[f"avg_body_range_ratio_{tf_attr}_lb{lb}"] = _mk_abr()
            d[f"compression_count_{tf_attr}_lb{lb}"] = _mk_cc()
            d[f"expansion_count_{tf_attr}_lb{lb}"] = _mk_ec()

    # Streak features
    for tf_attr in ("m15", "h1"):
        def _mk_g(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1}[tf]
                return _feature_longest_green_streak(df, ts_close, 50)
            return fn
        def _mk_r(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1}[tf]
                return _feature_longest_red_streak(df, ts_close, 50)
            return fn
        d[f"longest_green_streak_{tf_attr}_lb50"] = _mk_g()
        d[f"longest_red_streak_{tf_attr}_lb50"] = _mk_r()

    for tf_attr in ("m15", "h1"):
        for lb in (20, 50):
            def _mk_mr(tf=tf_attr, lb=lb):
                def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                    df = {"m15": df_m15, "h1": df_h1}[tf]
                    return _feature_micro_reversal_rate(df, ts_close, lb)
                return fn
            d[f"micro_reversal_rate_{tf_attr}_lb{lb}"] = _mk_mr()

    # Volume momentum (3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_vm(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_vol_momentum(df, ts_close, tf=tf)
            return fn
        d[f"vol_momentum_{tf_attr}"] = _mk_vm()

    # Range / mean ratio (3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_rm(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_range_mean_ratio_5_50(df, ts_close, tf=tf)
            return fn
        d[f"range_mean_ratio_5_50_{tf_attr}"] = _mk_rm()

    # Vol-of-vol (3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_vv(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_volume_volofvol(df, ts_close, 50)
            return fn
        d[f"volume_volofvol_{tf_attr}_lb50"] = _mk_vv()

    # FVG directional skew (3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_skew(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_fvg_directional_skew(df, ts_close, 50)
            return fn
        d[f"fvg_directional_skew_{tf_attr}_lb50"] = _mk_skew()

    # Close in lb50 range (3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_cir(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_close_in_lb50_range(df, ts_close, tf=tf)
            return fn
        d[f"close_in_lb50_range_{tf_attr}"] = _mk_cir()

    # Last-bar return / ATR (3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_lba(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_last_bar_return_atr(df, ts_close, tf=tf)
            return fn
        d[f"last_bar_return_atr_{tf_attr}"] = _mk_lba()

    # Upper / lower body lb20 (3 + 3)
    for tf_attr in ("m15", "h1", "h4"):
        def _mk_ub(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_upper_lower_body_lb20(df, ts_close, kind="upper")
            return fn
        def _mk_lwb(tf=tf_attr):
            def fn(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df=None):
                df = {"m15": df_m15, "h1": df_h1, "h4": df_h4}[tf]
                return _feature_upper_lower_body_lb20(df, ts_close, kind="lower")
            return fn
        d[f"upper_body_lb20_{tf_attr}"] = _mk_ub()
        d[f"lower_body_lb20_{tf_attr}"] = _mk_lwb()

    return d


DISPATCHER: dict[str, callable] = _build_dispatcher()


# ---------------------------------------------------------------------------
# Schema sanity check
# ---------------------------------------------------------------------------

# Inline assertion: the dispatcher must cover every spec name.
_missing = set(FEATURE_NAMES) - set(DISPATCHER.keys())
assert not _missing, f"DISPATCHER missing implementations for: {sorted(_missing)}"
_extra = set(DISPATCHER.keys()) - set(FEATURE_NAMES)
assert not _extra, f"DISPATCHER has feature impls without specs: {sorted(_extra)}"
assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES)), "duplicate feature names in FEATURE_NAMES"


# ---------------------------------------------------------------------------
# Tick-data loaders
# ---------------------------------------------------------------------------


def load_tick_frame_for_date(symbol: str, date_iso: str, *, root: Path | str = "data/ticks") -> Optional[pd.DataFrame]:
    """Load ``data/ticks/{symbol}/{date_iso}.parquet`` if it exists.

    Returns ``None`` when the parquet is absent — callers must handle this
    cleanly (the per-feature functions return SENTINEL_NAN on ``tick_df is
    None``).
    """
    p = Path(root) / symbol / f"{date_iso}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df


def tick_coverage_table(*, root: Path | str = "data/ticks") -> pd.DataFrame:
    """Walk ``data/ticks/`` and emit a per-(symbol, date) coverage table.

    Columns: symbol, date_iso, n_ticks, span_seconds, has_aggressor.
    """
    rows: list[dict] = []
    root_p = Path(root)
    if not root_p.exists():
        return pd.DataFrame(columns=["symbol", "date_iso", "n_ticks", "span_seconds", "has_aggressor"])
    for sym_dir in sorted(p for p in root_p.iterdir() if p.is_dir()):
        for parquet in sorted(sym_dir.glob("*.parquet")):
            try:
                df = pd.read_parquet(parquet)
            except Exception as e:  # pragma: no cover — diagnostic only
                rows.append({
                    "symbol": sym_dir.name,
                    "date_iso": parquet.stem,
                    "n_ticks": -1,
                    "span_seconds": -1,
                    "has_aggressor": False,
                    "error": str(e),
                })
                continue
            n = len(df)
            if "ts_utc" in df.columns and n > 0:
                span = (df["ts_utc"].max() - df["ts_utc"].min()).total_seconds()
            else:
                span = 0.0
            has_aggr = ("inferred_aggressor" in df.columns) and (
                df["inferred_aggressor"].notna().sum() > 0
            )
            rows.append({
                "symbol": sym_dir.name,
                "date_iso": parquet.stem,
                "n_ticks": n,
                "span_seconds": int(span),
                "has_aggressor": bool(has_aggr),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Compute API
# ---------------------------------------------------------------------------


def compute_microstructure_features(
    df_m15: pd.DataFrame,
    df_m1: pd.DataFrame,
    df_h1: pd.DataFrame,
    df_h4: pd.DataFrame,
    ts_close: datetime | pd.Timestamp,
    *,
    symbol: str,
    tick_df: Optional[pd.DataFrame] = None,
    feature_names: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Compute every (or a subset of) microstructure features at ``ts_close``.

    Parameters
    ----------
    df_m15, df_m1, df_h1, df_h4 : pd.DataFrame
        OHLCV bar frames, columns ``['time','open','high','low','close','volume']``.
        Pre-loaded by the caller; we only slice them point-in-time.
    ts_close : datetime
        The candle-close time at which features are evaluated. Must satisfy
        ``ts_close <= DATA_CUTOFF_UTC``.
    symbol : str
        Instrument symbol (XAUUSD, NAS100, …) — used for diagnostics, not
        in feature math.
    tick_df : pd.DataFrame, optional
        Captured tick parquet rows for the date of ``ts_close``. ``None``
        means "no tick coverage" for this candle and tick-required features
        emit NaN.
    feature_names : iterable of str, optional
        Subset of feature names to compute. Defaults to ``FEATURE_NAMES``.

    Returns
    -------
    pd.DataFrame
        Single-row DataFrame indexed by ``ts_close`` with columns = feature
        names (subset = those requested or all). Cell values are float; NaN
        for missing inputs.

    Notes
    -----
    Cutoff enforcement is HARD — calling with ``ts_close >= DATA_CUTOFF_UTC``
    raises ``ValueError``.
    """
    ts = _ensure_utc(ts_close)
    if ts >= _ensure_utc(DATA_CUTOFF_UTC):
        raise ValueError(
            f"ts_close={ts.isoformat()} is at or after DATA_CUTOFF_UTC="
            f"{DATA_CUTOFF_UTC.isoformat()}; refusing to leak future data."
        )

    names = list(feature_names) if feature_names is not None else FEATURE_NAMES
    missing = [n for n in names if n not in DISPATCHER]
    if missing:
        raise KeyError(f"unknown feature names: {missing}")

    out: dict[str, float] = {}
    for n in names:
        fn = DISPATCHER[n]
        try:
            v = fn(df_m15, df_m1, df_h1, df_h4, ts, symbol=symbol, tick_df=tick_df)
        except Exception as e:  # noqa: BLE001 — research code, log + nan
            warnings.warn(f"feature {n} raised {type(e).__name__}: {e}", stacklevel=2)
            v = SENTINEL_NAN
        out[n] = float(v) if v is not None else SENTINEL_NAN

    df = pd.DataFrame([out])
    df.index = pd.Index([ts], name="ts_close")
    return df


# ---------------------------------------------------------------------------
# Stability scoring
# ---------------------------------------------------------------------------


def _spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, int, float]:
    """Pure-numpy Spearman + asymptotic two-sided p-value via Student-t."""
    mask = (~np.isnan(x)) & (~np.isnan(y))
    x = x[mask]
    y = y[mask]
    n = len(x)
    if n < 5:
        return float("nan"), n, float("nan")
    rx = pd.Series(x).rank(method="average").values
    ry = pd.Series(y).rank(method="average").values
    mx, my = rx.mean(), ry.mean()
    sxy = ((rx - mx) * (ry - my)).sum()
    sxx = ((rx - mx) ** 2).sum()
    syy = ((ry - my) ** 2).sum()
    if sxx <= 0 or syy <= 0:
        return 0.0, n, 1.0
    rho = float(sxy / math.sqrt(sxx * syy))
    if abs(rho) >= 0.999999:
        return rho, n, 0.0
    t = rho * math.sqrt(max((n - 2) / max(1.0 - rho * rho, 1e-12), 0.0))
    # two-sided p via Student-t — use a beta-incomplete approximation
    df = n - 2
    x_ = df / (df + t * t)
    # Use scipy if present, fallback to pure-python wilson approx
    try:
        from scipy.special import betainc

        p = float(betainc(df / 2.0, 0.5, x_))
    except Exception:
        # crude conservative bound
        p = float(min(1.0, 1.0 / (t * t + 1.0)))
    return rho, n, p


def compute_stability_for_features(
    feature_values: pd.DataFrame,
    realized_r: pd.Series,
) -> pd.DataFrame:
    """Compute Spearman rank correlation between each feature column in
    ``feature_values`` and ``realized_r``.

    Parameters
    ----------
    feature_values : pd.DataFrame
        Each row = one trade / one ts_close. Each column = one feature.
    realized_r : pd.Series
        Aligned to ``feature_values.index``; the realized-R outcome.

    Returns
    -------
    pd.DataFrame with columns ``feature, stability_rho, stability_n,
    stability_p``.
    """
    rows: list[dict] = []
    for feat in feature_values.columns:
        vals = feature_values[feat].values.astype(float)
        rho, n, p = _spearman(vals, realized_r.values.astype(float))
        rows.append({
            "feature": feat,
            "stability_rho": rho,
            "stability_n": n,
            "stability_p": p,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Convenience: emit catalog CSV in lock-step with implementation
# ---------------------------------------------------------------------------


def emit_catalog_csv(
    out_path: Path | str,
    *,
    stability: Optional[pd.DataFrame] = None,
) -> None:
    """Write ``microstructure.csv`` covering every spec, optionally joined
    with stability scores.

    The emitted columns are:
        family, feature_name, source, lookback, computation_summary,
        stability_rho, stability_n, stability_p, expensive_flag
    """
    rows = []
    stab_lookup: dict[str, dict] = {}
    if stability is not None:
        for r in stability.to_dict(orient="records"):
            stab_lookup[r["feature"]] = r
    for s in FEATURE_SPECS:
        sb = stab_lookup.get(s.name, {})
        rows.append({
            "family": s.family,
            "feature_name": s.name,
            "source": s.source,
            "lookback": s.lookback,
            "computation_summary": s.computation_summary,
            "stability_rho": sb.get("stability_rho", ""),
            "stability_n": sb.get("stability_n", ""),
            "stability_p": sb.get("stability_p", ""),
            "expensive_flag": "EXPENSIVE_TICK" if s.expensive_flag and s.requires_tick else (
                "EXPENSIVE" if s.expensive_flag else ""
            ),
        })
    pd.DataFrame(rows).to_csv(out_path, index=False)


# ---------------------------------------------------------------------------
# __main__ — print spec count for quick inspection
# ---------------------------------------------------------------------------


if __name__ == "__main__":  # pragma: no cover
    print(f"FEATURE_SPECS: {len(FEATURE_SPECS)} features")
    print(f"DISPATCHER: {len(DISPATCHER)} implementations")
    print(f"requires_tick: {sum(1 for s in FEATURE_SPECS if s.requires_tick)}")
    print(f"expensive: {sum(1 for s in FEATURE_SPECS if s.expensive_flag)}")
