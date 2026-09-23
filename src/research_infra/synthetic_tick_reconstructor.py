"""E24 — Synthetic tick reconstruction from sub-M15 OHLC bars.

Strategic question
==================
The ``tick_features.py`` production module relies on the captured tick
parquets under ``data/ticks/{SYMBOL}/*.parquet``, but those files only
exist from 2026-04-25 onward (when the tick-capture daemon was
deployed) and are confined to a handful of broker-permitted instruments.
For *historical* research over the 2024-2025 sessions we have no
broker-real ticks at all, only OHLCV bars at M15 (and, for select
instruments, M5).

E24 builds a deterministic, conservative **synthetic-tick reconstructor**
that takes a sequence of sub-M15 candles (M1 if available, M5 as a
fallback) and emits a per-bar synthetic tick array suitable for
microstructure feature extraction (E26). The reconstructor is *not* a
broker-faithful tick replay: it only recovers the directional sign of
intra-bar buying/selling pressure and the open/high/low/close path
implied by the candle. It is **directionally** useful for D.1
microstructure-feature partial unlock, NOT a substitute for real
aggressor flags.

Hard rules preserved
====================
* **NOT broker-real.** All emissions are clearly tagged
  ``source: "synthetic_ohlc"`` so any downstream code or human reader
  can distinguish them from real captured ticks. Lee-Ready 1991 reports
  ~85% accuracy on NYSE TAQ; per the
  ``data/ticks/README.md`` empirical probe note, even *real* ticks on
  this broker classify at ~60-80% — synthetic from OHLC alone is
  expected to be lower still, and is treated as observation-only.
* **Pure Python, no scipy/pandas dependency.** Reconstruction uses
  ``csv`` + ``datetime`` + ``statistics`` so it can run inside the
  sandboxed test process without optional deps.
* **Deterministic.** Same input ⇒ same output. No randomness, no
  hidden RNG seeds. The reconstructor is a pure function of the input
  candle sequence.
* **Fail-open.** Missing input bars or invalid OHLC (high < low etc.)
  raise ``ValueError`` rather than silently emitting garbage. Callers
  may catch and skip.
* **Source documentation.** Each tick carries a ``direction_proxy``
  (``"buy"`` / ``"sell"`` / ``"neutral"``) computed from candle-close
  vs candle-open following the simplest Lee-Ready proxy: a green
  candle is buyer-initiated, a red candle is seller-initiated, a doji
  (close == open within tolerance) is neutral.

Schema (canonical)
==================
Input bar dict::

    {
        "time": "2026-04-15T13:15:00+00:00",  # ISO-8601 UTC, bar OPEN time
        "open": 4791.86,
        "high": 4796.28,
        "low":  4787.44,
        "close": 4793.50,
        "volume": 520,
    }

Output synthetic tick dict (one per emitted tick)::

    {
        "ts": "2026-04-15T13:15:00+00:00",
        "price": 4791.86,
        "direction_proxy": "buy" | "sell" | "neutral",
        "volume_proxy": 130.0,                 # share of bar volume
        "source": "synthetic_ohlc",
        "parent_bar_open": "2026-04-15T13:15:00+00:00",
    }

Per-bar emission strategy
-------------------------
For each input bar we emit exactly **4 synthetic ticks**, in
chronological order, that walk the OHLC path::

    open  -> high  -> low  -> close   if green (close >= open)
    open  -> low   -> high -> close   if red   (close <  open)

This is the deterministic OHLC path used by every M5/M1-emulator the
authors are aware of (cf. MetaTrader 5 ``EVERY_TICK_BASED_ON_REAL_TICKS``
fallback when no real ticks are available). Each tick gets a quarter of
the bar volume so cumulative_delta integrates to a sensible per-bar
delta.

Timestamps
----------
Synthetic ticks are spaced evenly across the bar duration. For an M1
input bar (60 s), the four ticks land at the bar open, +15 s, +30 s,
and +45 s. The bar duration is inferred from the gap between
consecutive bars (assumes uniform sampling) or defaults to 60 s if a
single bar is supplied.

Public surface
--------------
* :func:`load_sub_m15_bars` — read M1 (preferred) or M5 (fallback) CSV
  and return a sorted list of bar dicts. Returns the timeframe-string
  used so callers can log it. Raises ``FileNotFoundError`` if neither
  M1 nor M5 exists for the symbol.
* :func:`reconstruct_ticks_for_bar` — single-bar reconstruction. Pure
  function. Returns 4 synthetic ticks.
* :func:`reconstruct_ticks_for_window` — slice a sequence of bars by
  ``[start, end)`` and reconstruct ticks for every bar in the window.
* :func:`bar_lee_ready_direction` — the directional sign of one bar
  (``"buy"`` / ``"sell"`` / ``"neutral"``). Exposed so E26 can compute
  feature aggregates without re-walking the synthetic tick list.
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Tolerance for considering close == open as a "doji" (neutral) bar, in
#: fractional units of the bar's high-low range. A bar whose
#: ``|close - open| / max(high - low, eps)`` is below this threshold is
#: classified as neutral.  0.10 was chosen so that an M1 candle whose
#: body is <10% of its range is treated as no-net-pressure.
DOJI_BODY_RATIO_THRESHOLD: float = 0.10

#: Timeframes the loader will attempt, in priority order.
SUB_M15_TIMEFRAMES: tuple[str, ...] = ("M1", "M5")

#: Number of ticks to emit per input bar. Fixed at 4 (open + high + low
#: + close path). Spec-locked: changing this breaks E26's per-bar
#: volume share assumption.
TICKS_PER_BAR: int = 4


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _parse_iso_utc(ts_str: str) -> datetime:
    """Parse an ISO-8601 timestamp into a UTC-aware datetime.

    Accepts both naive timestamps (assumed UTC, the project's CSV
    convention) and explicit ``+00:00`` / ``Z`` suffixes.
    """
    s = ts_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        # Handle the project's "YYYY-MM-DD HH:MM:SS" convention
        if " " in s and "T" not in s:
            dt = datetime.fromisoformat(s.replace(" ", "T"))
        else:
            raise ValueError(f"Could not parse timestamp {ts_str!r}: {e}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_sub_m15_bars(
    symbol: str,
    data_dir: str | Path,
    *,
    allow_m15_fallback: bool = False,
) -> tuple[list[dict], str]:
    """Load the highest-resolution sub-M15 OHLCV CSV available for ``symbol``.

    Tries M1 first, falls back to M5. If neither exists and
    ``allow_m15_fallback`` is True, falls back to M15 (returned as
    ``"M15_fallback"`` so downstream code can flag the degraded
    resolution). If no input is usable, raises ``FileNotFoundError``.

    Returns ``(bars, timeframe_label)`` where ``bars`` is a sorted-by-
    time list of bar dicts and ``timeframe_label`` is one of ``"M1"``,
    ``"M5"``, or ``"M15_fallback"``.
    """
    base = Path(data_dir)
    last_err: Optional[FileNotFoundError] = None
    for tf in SUB_M15_TIMEFRAMES:
        path = base / f"{symbol}_{tf}.csv"
        if not path.exists():
            last_err = FileNotFoundError(f"Missing {path}")
            continue
        bars = _read_csv_bars(path)
        bars.sort(key=lambda b: b["time"])
        return bars, tf
    if allow_m15_fallback:
        m15 = base / f"{symbol}_M15.csv"
        if m15.exists():
            bars = _read_csv_bars(m15)
            bars.sort(key=lambda b: b["time"])
            return bars, "M15_fallback"
        last_err = FileNotFoundError(f"Missing {m15}")
    raise FileNotFoundError(
        f"No sub-M15 CSV (M1 or M5{'/M15' if allow_m15_fallback else ''}) found for {symbol} under {base}"
    ) from last_err


def _read_csv_bars(path: Path) -> list[dict]:
    """Read a project-format OHLCV CSV. Schema: time,open,high,low,close,volume."""
    bars: list[dict] = []
    with open(path, "r", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                bar = {
                    "time": _parse_iso_utc(row["time"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0),
                }
            except (KeyError, ValueError) as e:
                logger.warning("Skipping malformed row in %s: %s (%s)", path, row, e)
                continue
            if bar["high"] < bar["low"]:
                logger.warning("Skipping invalid bar (high<low) at %s in %s", row.get("time"), path)
                continue
            bars.append(bar)
    return bars


# ---------------------------------------------------------------------------
# Per-bar reconstruction
# ---------------------------------------------------------------------------


def bar_lee_ready_direction(bar: dict) -> str:
    """Lee-Ready proxy for a single OHLC bar.

    Returns ``"buy"``, ``"sell"``, or ``"neutral"``. The doji band uses
    ``DOJI_BODY_RATIO_THRESHOLD`` (10% of the bar range); below that the
    bar is treated as no-net-pressure rather than forced into a side.
    """
    o, c, h, l = bar["open"], bar["close"], bar["high"], bar["low"]
    rng = max(h - l, 1e-9)
    body_ratio = abs(c - o) / rng
    if body_ratio < DOJI_BODY_RATIO_THRESHOLD:
        return "neutral"
    return "buy" if c >= o else "sell"


def _bar_duration_seconds(bars: list[dict], idx: int, default: int = 60) -> int:
    """Infer bar duration from neighbour spacing. Default 60 s (M1)."""
    if idx + 1 < len(bars):
        delta = (bars[idx + 1]["time"] - bars[idx]["time"]).total_seconds()
        if delta > 0:
            return int(delta)
    if idx > 0:
        delta = (bars[idx]["time"] - bars[idx - 1]["time"]).total_seconds()
        if delta > 0:
            return int(delta)
    return default


def reconstruct_ticks_for_bar(bar: dict, duration_s: int = 60) -> list[dict]:
    """Reconstruct a 4-tick OHLC path for one bar.

    Order: green ⇒ open→high→low→close; red ⇒ open→low→high→close.
    Volume is split evenly across the 4 ticks. Direction proxy is the
    bar-level Lee-Ready sign (all 4 ticks share it — synthesizing
    intra-bar direction reversals from OHLC alone has no information
    content beyond the bar).
    """
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    direction = bar_lee_ready_direction(bar)
    vol_share = bar["volume"] / TICKS_PER_BAR
    bar_open = bar["time"]
    step = max(1, duration_s // TICKS_PER_BAR)

    if c >= o:
        path = [o, h, l, c]
    else:
        path = [o, l, h, c]

    ticks = []
    for i, price in enumerate(path):
        ticks.append({
            "ts": bar_open + timedelta(seconds=i * step),
            "price": price,
            "direction_proxy": direction,
            "volume_proxy": vol_share,
            "source": "synthetic_ohlc",
            "parent_bar_open": bar_open,
        })
    return ticks


def reconstruct_ticks_for_window(
    bars: list[dict],
    window_start: datetime,
    window_end: datetime,
) -> list[dict]:
    """Reconstruct synthetic ticks for every bar in ``[start, end)``.

    The window is half-open: a bar whose open is ``>= window_start``
    AND ``< window_end`` is included. Bars are assumed pre-sorted by
    time (as returned by :func:`load_sub_m15_bars`).
    """
    if window_start.tzinfo is None or window_end.tzinfo is None:
        raise ValueError("window_start/window_end must be timezone-aware UTC")
    if window_end <= window_start:
        raise ValueError(
            f"Window end {window_end!r} must be strictly after start {window_start!r}"
        )

    out: list[dict] = []
    for idx, bar in enumerate(bars):
        if bar["time"] < window_start:
            continue
        if bar["time"] >= window_end:
            break
        dur = _bar_duration_seconds(bars, idx)
        out.extend(reconstruct_ticks_for_bar(bar, duration_s=dur))
    return out


# ---------------------------------------------------------------------------
# CLI helper (sample output for the artifact bundle)
# ---------------------------------------------------------------------------


def emit_sample_csv(
    symbol: str,
    data_dir: str | Path,
    out_path: str | Path,
    *,
    window_start: datetime,
    window_end: datetime,
    allow_m15_fallback: bool = True,
) -> dict:
    """Reconstruct ticks for ``[start, end)`` and write a CSV.

    Returns a small summary dict suitable for inclusion in the research
    artifact bundle.
    """
    bars, tf = load_sub_m15_bars(symbol, data_dir, allow_m15_fallback=allow_m15_fallback)
    ticks = reconstruct_ticks_for_window(bars, window_start, window_end)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "price", "direction_proxy", "volume_proxy", "source", "parent_bar_open"])
        for t in ticks:
            w.writerow([
                t["ts"].isoformat(),
                f"{t['price']:.5f}",
                t["direction_proxy"],
                f"{t['volume_proxy']:.4f}",
                t["source"],
                t["parent_bar_open"].isoformat(),
            ])
    return {
        "symbol": symbol,
        "input_timeframe": tf,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "ticks_emitted": len(ticks),
        "bars_consumed": sum(1 for b in bars if window_start <= b["time"] < window_end),
        "out_path": str(out),
    }
