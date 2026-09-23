"""Per-M15-bar Tick Feature Extractor.

Reads the tick parquet files written by ``tick_capture.py`` and computes
8-12 microstructure features per closing M15 bar. Emits a sidecar JSON file
under ``pipeline_state/03_tick_features_{symbol}_{candle_time}.json`` for
downstream consumption by ``data_ingestion.ingest_live_data``.

Design intent
-------------
This module is the **read** side of the tick pipeline. ``tick_capture.py``
writes parquet files asynchronously; this module reads them on M15 candle
close, slices to the just-closed [bar_open_utc, bar_close_utc) window,
computes features, and writes a small JSON sidecar.

If no tick file is available (daemon not running, tick file missing, parsing
error), this module returns ``None`` rather than raising — callers must handle
None gracefully (log warning, proceed without tick features). This is the
**fail-open** path required by the integration spec.

Feature schema
--------------
Each sidecar JSON has:

::

    {
      "schema_version": 1,
      "symbol": "XAUUSD",
      "candle_time_utc": "2026-04-25T13:15:00+00:00",
      "bar_open_utc": "2026-04-25T13:00:00+00:00",
      "bar_close_utc": "2026-04-25T13:15:00+00:00",
      "n_ticks": 1842,
      "features": {
        "cumulative_delta": 124.5,
        "max_delta_within_bar": 187.0,
        "min_delta_within_bar": -38.0,
        "footprint_imbalance": 0.74,
        "spread_spike_count": 3,
        "micro_reversal_count": 2,
        "tick_velocity": 2.05,
        "aggressor_balance": 0.61,
        "cvd_divergence_flag": false,
        "buy_pct": 0.61,
        "spread_max_cents": 0.42,
        "spread_close_cents": 0.18
      }
    }

Feature definitions
-------------------

- **cumulative_delta** — Sum over all ticks in the bar of
  ``volume_signed = +volume`` if aggressor=="buy", ``-volume`` if "sell",
  ``0`` if "neutral". On spot CFDs where ``volume`` is 0 or 1, this collapses
  to a count delta (buy_count − sell_count). When ``volume_real``-style data
  is available (futures via Databento, future migration path), this becomes
  authentic signed-volume.
- **max_delta_within_bar / min_delta_within_bar** — Peak running delta
  (cumulative delta over the in-bar tick sequence). High max + negative min
  signals two-sided fight; close_delta == max_delta signals one-sided trend.
- **footprint_imbalance** — Per-price-bucket (1¢ for XAU, 1pip for FX),
  ``max(abs(buy_vol - sell_vol) / total_vol)`` across all buckets touched.
  Range [0, 1]. 1.0 = at least one price level had pure one-sided volume.
- **spread_spike_count** — Number of ticks where ``(ask - bid)`` exceeds
  ``2 ×`` rolling-100 spread median over the bar's tick stream. Captures
  liquidity withdrawal events (news, manipulation, flash dislocations).
- **micro_reversal_count** — Number of intra-bar excursions where price
  travels at least 0.5 × (bar_high - bar_low) and reverses. Captures
  chop / stop-hunt patterns invisible at M15 OHLC.
- **tick_velocity** — Mean ticks per second over the bar. Baseline-normalized
  via ``tick_velocity_norm`` if a baseline is provided (currently raw value).
- **aggressor_balance** — ``buy_volume / total_volume``. Range [0, 1].
  0.5 = balanced. >0.6 sustained = strong buying pressure.
- **cvd_divergence_flag** — True if the sign of (close - open) DISAGREES with
  the sign of cumulative_delta. Classic absorption signal — price moves one
  way while flow moves the other.
- **buy_pct** — Buy-tick count / classifiable-tick count. Differs from
  ``aggressor_balance`` (which is volume-weighted) when volumes are non-uniform.
- **spread_max_cents** — Max spread observed during the bar (centred — for FX
  the unit is "cents" only nominal; treat as instrument-native multiplied by 100).
- **spread_close_cents** — Spread at the last tick in the bar.

Edge cases
----------

- **Empty bar** (zero ticks): all features set to 0 or null; ``n_ticks: 0``.
- **Single tick**: ``cumulative_delta`` = ±volume, ``max_delta`` =
  ``min_delta`` = ``cumulative_delta``; reversal_count = 0.
- **All-mid ticks** (every aggressor == "neutral"): ``cumulative_delta`` = 0,
  ``aggressor_balance`` defined only on classifiable ticks (returned as
  ``null`` if all neutral).
- **NaN / corrupt rows**: filtered out before feature computation.
"""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default storage roots (overridable for tests).
TICKS_ROOT = Path("data/ticks")
SIDECAR_ROOT = Path("pipeline_state")

SCHEMA_VERSION = 1

# Spread-spike threshold: tick spread > THRESHOLD_MULT × rolling spread median.
SPREAD_SPIKE_THRESHOLD_MULT = 2.0

# Micro-reversal threshold (fraction of bar high-low range).
MICRO_REVERSAL_FRAC = 0.5

# Default M15 bar length in seconds.
M15_SECONDS = 15 * 60

# Per-instrument price bucket size for footprint imbalance.
# Values calibrated to roughly equal granularity (5-15 buckets per typical M15
# range): for XAU $0.10, indices 1pt, JPY pairs 0.01, GBPUSD 0.0001.
PRICE_BUCKET_SIZE = {
    "XAUUSD": 0.10,
    "US30_cash": 1.0,
    "US30": 1.0,
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "GBPUSD": 0.0001,
}
DEFAULT_PRICE_BUCKET = 0.10


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------


@dataclass
class TickFeatures:
    """Per-bar tick feature record. All fields are JSON-serializable."""

    schema_version: int
    symbol: str
    candle_time_utc: str
    bar_open_utc: str
    bar_close_utc: str
    n_ticks: int
    features: dict

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str, indent=2)


# ---------------------------------------------------------------------------
# Bar-window math
# ---------------------------------------------------------------------------


def m15_bar_window(candle_time_utc: datetime) -> tuple[datetime, datetime]:
    """Return ``(bar_open_utc, bar_close_utc)`` for an M15 candle close time.

    Convention: ``candle_time_utc`` is the bar CLOSE time. Bar opens 15 minutes
    earlier. We snap to the M15 grid (e.g., 13:00, 13:15, 13:30, 13:45).
    """
    # Snap to nearest M15 boundary.
    minute = candle_time_utc.minute
    snapped = candle_time_utc.replace(
        minute=(minute // 15) * 15, second=0, microsecond=0,
    )
    # If candle_time_utc is the close, bar opened 15 min before.
    bar_close = snapped
    bar_open = snapped - timedelta(seconds=M15_SECONDS)
    return bar_open, bar_close


# ---------------------------------------------------------------------------
# Tick I/O
# ---------------------------------------------------------------------------


def _read_ticks_for_bar(symbol: str, bar_open: datetime, bar_close: datetime,
                         ticks_root: Path = TICKS_ROOT):
    """Read tick rows for ``[bar_open, bar_close)`` from daily Parquet file(s).

    Returns a pandas DataFrame, possibly empty. Returns ``None`` if pyarrow/
    pandas unavailable OR if no day file exists for the bar's UTC date(s).
    """
    try:
        import pandas as pd
        import pyarrow.parquet as pq
    except ImportError:
        logger.warning("pyarrow/pandas missing — tick features unavailable")
        return None

    # A bar can straddle a UTC day at most at midnight; check both possible files.
    days = sorted({bar_open.date(), (bar_close - timedelta(microseconds=1)).date()})
    frames = []
    for day in days:
        path = ticks_root / symbol / f"{day.isoformat()}.parquet"
        if not path.exists():
            continue
        try:
            df = pq.read_table(str(path)).to_pandas()
            frames.append(df)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to read %s: %s", path, e)

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    if df.empty or "ts_utc" not in df.columns:
        return df.iloc[0:0]  # empty but well-typed

    # Ensure tz-aware.
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    bar_open_ts = pd.Timestamp(bar_open).tz_convert("UTC") if pd.Timestamp(bar_open).tzinfo else pd.Timestamp(bar_open, tz="UTC")
    bar_close_ts = pd.Timestamp(bar_close).tz_convert("UTC") if pd.Timestamp(bar_close).tzinfo else pd.Timestamp(bar_close, tz="UTC")
    mask = (df["ts_utc"] >= bar_open_ts) & (df["ts_utc"] < bar_close_ts)
    return df.loc[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------


def _signed_volume(volume: float, aggressor: str) -> float:
    """Return signed volume per Lee-Ready aggressor classification."""
    if aggressor == "buy":
        return float(volume)
    if aggressor == "sell":
        return -float(volume)
    return 0.0


def _abs_volume(volume: float, aggressor: str) -> float:
    """Absolute volume (only counts classifiable buy/sell ticks)."""
    if aggressor in ("buy", "sell"):
        return abs(float(volume))
    return 0.0


def _empty_features() -> dict:
    """Default feature dict for empty / degenerate bars."""
    return {
        "cumulative_delta": 0.0,
        "max_delta_within_bar": 0.0,
        "min_delta_within_bar": 0.0,
        "footprint_imbalance": 0.0,
        "spread_spike_count": 0,
        "micro_reversal_count": 0,
        "tick_velocity": 0.0,
        "aggressor_balance": None,
        "cvd_divergence_flag": False,
        "buy_pct": None,
        "spread_max_cents": 0.0,
        "spread_close_cents": 0.0,
    }


def compute_features_from_df(df, symbol: str = "XAUUSD",
                                bar_seconds: float = M15_SECONDS,
                                bucket_size: Optional[float] = None) -> dict:
    """Compute the 12 features given a tick DataFrame.

    The DataFrame must have columns: ``ts_utc``, ``bid``, ``ask``, ``last``,
    ``volume``, ``flags``, ``inferred_aggressor``. NaN rows are filtered.

    Public for unit-testability — callers in production should use
    :func:`compute_for_bar` which handles the I/O.
    """
    if df is None:
        return _empty_features()

    # Filter NaN/corrupt rows. We REQUIRE bid + ask + aggressor.
    try:
        import pandas as pd
        df = df.dropna(subset=["bid", "ask"]).reset_index(drop=True)
    except Exception:  # noqa: BLE001
        # Bail to empty if pandas not available or malformed.
        return _empty_features()

    n = len(df)
    if n == 0:
        return _empty_features()

    bucket = bucket_size if bucket_size is not None else PRICE_BUCKET_SIZE.get(symbol, DEFAULT_PRICE_BUCKET)

    # Vectorized signed/abs volume.
    aggressor = df["inferred_aggressor"].astype(str).fillna("neutral").to_numpy()
    volume = df["volume"].astype(float).fillna(0.0).to_numpy()
    bid = df["bid"].astype(float).to_numpy()
    ask = df["ask"].astype(float).to_numpy()
    # Tick "price" for delta accounting: prefer ``last`` if non-zero, else mid.
    last = df["last"].astype(float).fillna(0.0).to_numpy() if "last" in df.columns else None
    mid = (bid + ask) / 2.0
    if last is not None:
        price = mid.copy()
        mask_last = last > 0
        price[mask_last] = last[mask_last]
    else:
        price = mid

    # Volume effective for delta: spot CFDs often have volume=0; substitute 1.0
    # so each tick contributes to delta as a count (matches Lee-Ready intent
    # for FX where ``volume`` is meaningless).
    vol_for_delta = volume.copy()
    vol_for_delta[vol_for_delta <= 0] = 1.0

    # Signed volume per tick.
    signed = vol_for_delta.copy()
    signed[aggressor == "sell"] *= -1.0
    signed[aggressor == "neutral"] = 0.0

    # Cumulative delta and running max/min.
    cum = signed.cumsum()
    cumulative_delta = float(cum[-1]) if n > 0 else 0.0
    max_delta = float(cum.max()) if n > 0 else 0.0
    min_delta = float(cum.min()) if n > 0 else 0.0

    # Aggressor balance / buy_pct.
    abs_vol = vol_for_delta.copy()
    abs_vol[aggressor == "neutral"] = 0.0
    total_classified_vol = float(abs_vol.sum())
    buy_vol = float(abs_vol[aggressor == "buy"].sum())
    n_buy = int((aggressor == "buy").sum())
    n_sell = int((aggressor == "sell").sum())
    n_classified = n_buy + n_sell

    aggressor_balance = (buy_vol / total_classified_vol) if total_classified_vol > 0 else None
    buy_pct = (n_buy / n_classified) if n_classified > 0 else None

    # Footprint imbalance: bucket prices, accumulate signed volume per bucket,
    # report max(|imbalance|/total_in_bucket).
    if n_classified > 0:
        try:
            buckets: dict = {}
            for i in range(n):
                if aggressor[i] == "neutral":
                    continue
                b = round(price[i] / bucket)
                v = vol_for_delta[i]
                buy_b, sell_b = buckets.get(b, (0.0, 0.0))
                if aggressor[i] == "buy":
                    buy_b += v
                else:
                    sell_b += v
                buckets[b] = (buy_b, sell_b)
            max_imb = 0.0
            for buy_b, sell_b in buckets.values():
                t = buy_b + sell_b
                if t > 0:
                    imb = abs(buy_b - sell_b) / t
                    if imb > max_imb:
                        max_imb = imb
            footprint_imbalance = float(max_imb)
        except Exception:  # noqa: BLE001
            footprint_imbalance = 0.0
    else:
        footprint_imbalance = 0.0

    # Spread series.
    spread = ask - bid
    spread_max = float(spread.max()) if n > 0 else 0.0
    spread_close = float(spread[-1]) if n > 0 else 0.0

    # Spread spike count: rolling-100 median, >2x.
    if n >= 5:
        try:
            import numpy as np
            window = min(100, n)
            # Rolling median requires pandas for clean tail handling.
            rolling = pd.Series(spread).rolling(window=window, min_periods=5).median()
            # Replace NaN at the head with the median of the first ``window`` rows.
            head_median = float(np.median(spread[:window])) if window > 0 else 0.0
            rolling = rolling.fillna(head_median)
            threshold = SPREAD_SPIKE_THRESHOLD_MULT * rolling.to_numpy()
            spread_spike_count = int((spread > threshold).sum())
        except Exception:  # noqa: BLE001
            spread_spike_count = 0
    else:
        spread_spike_count = 0

    # Micro reversal count.
    bar_high = float(price.max())
    bar_low = float(price.min())
    bar_range = bar_high - bar_low
    if bar_range > 0 and n >= 3:
        threshold_dist = MICRO_REVERSAL_FRAC * bar_range
        micro_reversal_count = _count_micro_reversals(price, threshold_dist)
    else:
        micro_reversal_count = 0

    # Tick velocity (ticks per second).
    if bar_seconds > 0:
        tick_velocity = float(n) / float(bar_seconds)
    else:
        tick_velocity = 0.0

    # CVD divergence flag.
    open_price = float(price[0])
    close_price = float(price[-1])
    price_change = close_price - open_price
    if abs(price_change) > 1e-9 and abs(cumulative_delta) > 1e-9:
        # Sign disagreement = divergence (absorption).
        cvd_divergence_flag = (price_change > 0) != (cumulative_delta > 0)
    else:
        cvd_divergence_flag = False

    return {
        "cumulative_delta": _safe_float(cumulative_delta),
        "max_delta_within_bar": _safe_float(max_delta),
        "min_delta_within_bar": _safe_float(min_delta),
        "footprint_imbalance": _safe_float(footprint_imbalance),
        "spread_spike_count": int(spread_spike_count),
        "micro_reversal_count": int(micro_reversal_count),
        "tick_velocity": _safe_float(tick_velocity),
        "aggressor_balance": _safe_float(aggressor_balance) if aggressor_balance is not None else None,
        "cvd_divergence_flag": bool(cvd_divergence_flag),
        "buy_pct": _safe_float(buy_pct) if buy_pct is not None else None,
        "spread_max_cents": _safe_float(spread_max),
        "spread_close_cents": _safe_float(spread_close),
    }


def _safe_float(x) -> float:
    """Convert to float; replace NaN/inf with 0.0."""
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    except (TypeError, ValueError):
        return 0.0


def _count_micro_reversals(price, threshold_dist: float) -> int:
    """Count intra-bar excursions of at least ``threshold_dist`` that reverse.

    Algorithm (greedy zigzag):
      1. Track the running extreme (high or low) since the last "anchor."
      2. When price retraces by ≥ threshold_dist from the running extreme,
         count one reversal and re-anchor at the retracement extreme.
    """
    n = len(price)
    if n < 3 or threshold_dist <= 0:
        return 0

    count = 0
    direction = 0  # 0 = unknown, 1 = up-leg in progress, -1 = down-leg in progress
    anchor = float(price[0])
    extreme = float(price[0])

    for i in range(1, n):
        p = float(price[i])
        if direction == 0:
            # Establish initial direction by first move beyond noise.
            if p > anchor:
                direction = 1
                extreme = p
            elif p < anchor:
                direction = -1
                extreme = p
            continue

        if direction == 1:
            if p > extreme:
                extreme = p
            elif extreme - p >= threshold_dist:
                # Up-leg reversed.
                count += 1
                direction = -1
                anchor = extreme
                extreme = p
        else:  # direction == -1
            if p < extreme:
                extreme = p
            elif p - extreme >= threshold_dist:
                count += 1
                direction = 1
                anchor = extreme
                extreme = p

    return count


# ---------------------------------------------------------------------------
# Sidecar I/O
# ---------------------------------------------------------------------------


def sidecar_path_for(symbol: str, candle_time_utc: datetime,
                      sidecar_root: Path = SIDECAR_ROOT) -> Path:
    """Canonical sidecar path: ``pipeline_state/03_tick_features_{sym}_{ts}.json``."""
    ts = candle_time_utc.strftime("%Y%m%dT%H%M%S")
    return sidecar_root / f"03_tick_features_{symbol}_{ts}.json"


def write_sidecar(record: TickFeatures, sidecar_root: Path = SIDECAR_ROOT) -> Path:
    """Write a TickFeatures record atomically. Returns the path written."""
    candle_time = datetime.fromisoformat(record.candle_time_utc.replace("Z", "+00:00"))
    out_path = sidecar_path_for(record.symbol, candle_time, sidecar_root=sidecar_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + f".tmp{os.getpid()}")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(record.to_json())
    os.replace(str(tmp), str(out_path))
    return out_path


def read_sidecar(symbol: str, candle_time_utc: datetime,
                 sidecar_root: Path = SIDECAR_ROOT) -> Optional[dict]:
    """Read a sidecar JSON and return its dict, or None if missing/corrupt.

    Used by ``data_ingestion.ingest_live_data`` for the additive merge.
    """
    p = sidecar_path_for(symbol, candle_time_utc, sidecar_root=sidecar_root)
    if not p.exists():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not read tick sidecar %s: %s", p, e)
        return None


# ---------------------------------------------------------------------------
# Top-level extractor
# ---------------------------------------------------------------------------


def compute_for_bar(symbol: str, candle_time_utc: datetime,
                     ticks_root: Path = TICKS_ROOT,
                     write_to_sidecar: bool = True,
                     sidecar_root: Path = SIDECAR_ROOT) -> Optional[TickFeatures]:
    """Compute the per-bar feature set and optionally write a sidecar JSON.

    Parameters
    ----------
    symbol : str
        Canonical GTOS symbol.
    candle_time_utc : datetime
        M15 bar CLOSE time (timezone-aware UTC).
    ticks_root : Path
        Storage root for tick parquet files.
    write_to_sidecar : bool
        If True, persist the result to ``pipeline_state/`` before returning.
    sidecar_root : Path
        Override sidecar destination (tests pass tmp_path).

    Returns
    -------
    TickFeatures or None
        ``None`` if no tick data found / pyarrow missing — caller must
        handle gracefully.
    """
    if candle_time_utc.tzinfo is None:
        candle_time_utc = candle_time_utc.replace(tzinfo=timezone.utc)

    bar_open, bar_close = m15_bar_window(candle_time_utc)
    df = _read_ticks_for_bar(symbol, bar_open, bar_close, ticks_root=ticks_root)
    if df is None:
        # No data files at all for this bar.
        return None

    n_ticks = int(len(df))
    features = compute_features_from_df(
        df, symbol=symbol, bar_seconds=(bar_close - bar_open).total_seconds(),
    )
    record = TickFeatures(
        schema_version=SCHEMA_VERSION,
        symbol=symbol,
        candle_time_utc=candle_time_utc.isoformat(),
        bar_open_utc=bar_open.isoformat(),
        bar_close_utc=bar_close.isoformat(),
        n_ticks=n_ticks,
        features=features,
    )
    if write_to_sidecar:
        try:
            write_sidecar(record, sidecar_root=sidecar_root)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to write tick sidecar for %s @ %s: %s",
                            symbol, candle_time_utc, e)
    return record
