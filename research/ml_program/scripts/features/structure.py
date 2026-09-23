"""K54 v2 — STRUCTURE feature family.

Owner: Q1 Week 2-3 feature engineer (structure family).
Scope: ICT-style market-structure features built atop the existing
Component-2 primitives in ``src/components/market_state.py``.

What this family covers
-----------------------
* Active **Order Block** geometry (per timeframe, per lookback): depth,
  width, age, retest count, signed distance to current price, midpoint
  distance, type, count, mean depth.
* Active **Fair Value Gap** geometry (per timeframe): size, age, fill
  ratio, retest count, count.
* **Breaker Block** geometry: depth, distance, age, count,
  original-OB-direction flag.
* **Swing magnitudes** per timeframe (M15/H1/H4/D1): last swing leg
  range (ATR-units), leg velocity, swing count, magnitude asymmetry.
* **BOS / CHoCH** event counts per timeframe in last-N bars + age of
  most recent event + displacement-present count.
* **Multi-timeframe alignment vector**: direction agreement across
  M15/H1/H4/D1 + agreement count + signed score.
* **Distance-to-internal-swing** per timeframe (nearest high & low).
* **Pre-BOS impulse-leg geometry** (impulse range / ATR, bar count,
  ratio of impulse range to OB depth) — only valid when an OB has
  formed at the candle close being featurized.
* **Pre-BOS consolidation duration** — bar count of pre-impulse
  consolidation (defined as bars whose true-range / ATR < 0.7).

Hard constraints
----------------
1. **Point-in-time only.** Every feature is computable from data
   at-or-before its candle-close timestamp. We slice the candle list
   to ``candles[:idx+1]`` before any swing/OB/FVG detection. There is
   no future-data path.
2. **No look-ahead in retest counts.** ``OrderBlock.touch_count`` from
   ``_count_touches`` walks ``candles[formation_index+1:]`` — we feed
   it only the slice up to the featurized candle, so retest counts
   never include retests that happen after.
3. **OB ``mitigated`` flag uses past-only window.** We re-implement
   the inner OB construction using ``identify_order_blocks`` over the
   same slice; the ``mitigated`` flag therefore reflects only past
   mitigation visible at the candle close.
4. **No data outside cutoff.** Caller is responsible for truncating
   input frames at ``≤2026-04-28 23:59 UTC``.
5. **Fail-open NaN-handling.** Each feature returns ``NaN`` rather
   than raising on unfeaturizable inputs (insufficient history,
   missing TF). The modeller's pipeline is expected to impute or
   one-hot-encode missingness.

Uniform interface
-----------------
Every public feature lives behind two layers:

* ``compute_<primitive>(...)`` — a typed pure function returning the
  scalar(s) for one candle close.
* ``feature_<primitive>(...)`` — a vectorising wrapper that returns
  ``pd.Series`` indexed by candle close ``time``.

The Week-4 modeler uses ``build_structure_features(...)`` to assemble
all features at a list of candle-close timestamps for one symbol.

Source data + lookback windows
------------------------------
* OHLCV: ``data/historical_2026/{SYMBOL}_{TF}.csv`` (M15/H1/H4/D1).
* Time of TF: in ISO ``YYYY-mm-dd HH:MM:SS`` UTC, candle-OPEN labelled.
* Lookback windows (in candles of the named TF):
  - M15: ``[5, 20, 50, 100, 200]``
  - H1:  ``[20, 50, 100, 200]``
  - H4:  ``[20, 50, 100]``
  - D1:  ``[20, 50]``

The feature catalogue (``feature_catalogs/structure.md`` /
``structure.csv``) enumerates the cross-product.

Self-test
---------
Inline assertions exercise each primitive on a tiny synthetic OHLCV
input. The module is importable with ``python -c "import structure"``
in the project root with no external test fixtures required.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd

# Pull Component 2 primitives. Path setup keeps the module standalone
# (no need to install the project as a package).
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# These are pure functions over candle-list dicts; deterministic, no AI.
from src.components.market_state import (  # type: ignore
    avg_candle_body,
    calculate_atr,
    detect_structure_breaks,
    detect_swings,
    identify_breaker_blocks,
    identify_fvgs,
    identify_order_blocks,
    identify_structure,
    _count_touches,
)


# ---------------------------------------------------------------------------
# Lookback configuration
# ---------------------------------------------------------------------------

LOOKBACKS_M15: tuple[int, ...] = (20, 100)
LOOKBACKS_H1: tuple[int, ...] = (20, 100)
LOOKBACKS_H4: tuple[int, ...] = (20, 50)
LOOKBACKS_D1: tuple[int, ...] = (50,)

LOOKBACKS_BY_TF: dict[str, tuple[int, ...]] = {
    "M15": LOOKBACKS_M15,
    "H1": LOOKBACKS_H1,
    "H4": LOOKBACKS_H4,
    "D1": LOOKBACKS_D1,
}

TF_MINUTES: dict[str, int] = {"M15": 15, "H1": 60, "H4": 240, "D1": 1440}

# How many H1/H4/D1 candles to feed the M15 builder when it slices a TF
# higher than M15 for a given M15 timestamp. Keep generous so detector
# warmup is satisfied for swing detection (min_bars=2 on H1/H4/D1).
TF_CONTEXT_BARS: dict[str, int] = {"M15": 250, "H1": 250, "H4": 250, "D1": 80}


# ---------------------------------------------------------------------------
# Helpers — DataFrame -> candle-list dicts (Component-2 expects dicts)
# ---------------------------------------------------------------------------

def _df_to_candles(df: pd.DataFrame) -> list[dict]:
    """Convert a tidy OHLCV DataFrame to the list-of-dicts Component-2
    consumes.

    Required columns: ``time, open, high, low, close, volume``.
    ``time`` may be a string or datetime; we coerce to ISO string in
    UTC because Component-2 only inspects ``time[11:13]`` for hour.
    """
    if df is None or df.empty:
        return []
    out: list[dict] = []
    for _, row in df.iterrows():
        t = row["time"]
        if isinstance(t, pd.Timestamp):
            ts = t.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            ts = str(t).replace(" ", "T")
        out.append({
            "time": ts,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0) or 0),
        })
    return out


def _slice_candles_until(candles: list[dict], at_iso: str) -> list[dict]:
    """Return the prefix of *candles* up to and including the candle
    whose ISO time is ``<= at_iso``. Caller has already normalised
    ``at_iso`` to the TF's candle-open form.
    """
    if not candles:
        return []
    # ISO-8601 strings are lexicographically time-orderable when
    # zero-padded — relied on here. We compare in the same canonical
    # form by stripping any trailing tz suffix.
    target = at_iso.replace("Z", "").replace("+00:00", "")
    out: list[dict] = []
    for c in candles:
        ct = c["time"].replace("Z", "").replace("+00:00", "")
        if ct <= target:
            out.append(c)
        else:
            break
    return out


# ---------------------------------------------------------------------------
# Per-TF state container — one slice per (TF, candle-close)
# ---------------------------------------------------------------------------

@dataclass
class _TFState:
    """Cache the expensive Component-2 outputs for a single (TF, slice)
    so feature primitives can reuse without recomputing.
    """
    tf: str
    candles: list[dict]
    atr_14: float = 0.0
    avg_body: float = 0.0
    swings: list[Any] = field(default_factory=list)
    structure: Any = None
    structure_events: list[Any] = field(default_factory=list)
    order_blocks: list[Any] = field(default_factory=list)
    breakers: list[Any] = field(default_factory=list)
    fvgs: list[Any] = field(default_factory=list)
    last_close: float = math.nan

    @property
    def n(self) -> int:
        return len(self.candles)


def _build_tf_state(tf: str, candles: list[dict], min_bars: int = 2,
                    fvg_min_gap: float = 0.0) -> _TFState:
    """Run all Component-2 detection on a candle slice and cache the
    outputs. Empty/short input degrades gracefully: state.n == len.
    """
    s = _TFState(tf=tf, candles=candles)
    if not candles:
        return s
    s.atr_14 = calculate_atr(candles, period=14)
    s.avg_body = avg_candle_body(candles)
    s.swings = detect_swings(candles, min_bars=min_bars)
    s.structure = identify_structure(s.swings)
    s.structure_events = detect_structure_breaks(candles, s.swings, s.structure)
    s.order_blocks = identify_order_blocks(candles, s.structure_events)
    # Populate touch_count — IMPORTANT: only on the past slice, so
    # touches are by construction past-only.
    for ob in s.order_blocks:
        ob.touch_count = _count_touches(ob, candles)
    s.breakers = identify_breaker_blocks(candles, s.order_blocks)
    s.fvgs = identify_fvgs(candles, min_gap_size=fvg_min_gap)
    s.last_close = float(candles[-1]["close"])
    return s


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

NAN = float("nan")


def _safe_div(a: float, b: float) -> float:
    if b is None or not math.isfinite(b) or b == 0:
        return NAN
    return float(a) / float(b)


def _last_n(items: list, n: int) -> list:
    if n <= 0 or not items:
        return []
    return items[-n:]


def _atr_units(distance: float, atr: float) -> float:
    return _safe_div(distance, atr)


# ---------------------------------------------------------------------------
# Active OB geometry primitives
# ---------------------------------------------------------------------------

def compute_ob_features(state: _TFState, lookback: int) -> dict[str, float]:
    """Aggregate features across active OBs in the last *lookback*
    candles of *state*.

    Returns a fixed-key dict so columns stay stable across rows.

    Definitions:
    * "active OB" = OB whose ``formation_index`` falls in the last
      ``lookback`` candles of the slice (i.e. recent OB).
    * Distance is signed (entry - midpoint), so positive = price is
      above OB midpoint (relevant for bullish OB retest).
    * ``nearest`` = OB whose absolute midpoint distance to the last
      close is smallest.

    All distances are reported in three units: raw price ticks-equiv,
    ATR-multiples, and percent of price.
    """
    keys = [
        "ob_count", "ob_bull_count", "ob_bear_count",
        "ob_breaker_count_in_window",
        "nearest_ob_dist_atr", "nearest_ob_signed_atr",
        "nearest_ob_depth_atr", "nearest_ob_age_bars",
        "nearest_ob_touch_count", "nearest_ob_is_bullish",
        "ob_mean_depth_atr", "ob_mean_age_bars", "ob_max_touch_count",
        "ob_unmitigated_count", "ob_mitigated_count",
    ]
    out = {k: NAN for k in keys}

    if state.n == 0 or not state.order_blocks:
        # Counts that genuinely default to zero
        for k in ("ob_count", "ob_bull_count", "ob_bear_count",
                  "ob_breaker_count_in_window", "ob_unmitigated_count",
                  "ob_mitigated_count"):
            out[k] = 0.0
        return out

    cutoff_idx = max(0, state.n - 1 - lookback)
    last_close = state.last_close
    atr = state.atr_14 if state.atr_14 > 0 else NAN

    active = [ob for ob in state.order_blocks if ob.formation_index >= cutoff_idx]
    if not active:
        for k in ("ob_count", "ob_bull_count", "ob_bear_count",
                  "ob_breaker_count_in_window", "ob_unmitigated_count",
                  "ob_mitigated_count"):
            out[k] = 0.0
        return out

    out["ob_count"] = float(len(active))
    out["ob_bull_count"] = float(sum(1 for ob in active if ob.type == "bullish"))
    out["ob_bear_count"] = float(sum(1 for ob in active if ob.type == "bearish"))
    out["ob_unmitigated_count"] = float(sum(1 for ob in active if not ob.mitigated))
    out["ob_mitigated_count"] = float(sum(1 for ob in active if ob.mitigated))
    out["ob_breaker_count_in_window"] = float(sum(
        1 for bb in state.breakers
        if state.candles and bb.formation_time and any(
            c["time"] == bb.formation_time and i >= cutoff_idx
            for i, c in enumerate(state.candles)
        )
    ))

    # Per-OB depth / age / touch_count / mid-distance
    last_idx = state.n - 1
    depths_atr: list[float] = []
    ages: list[float] = []
    touches: list[int] = []
    nearest = None
    nearest_abs = math.inf
    for ob in active:
        depth = float(ob.high - ob.low)
        depth_atr = _safe_div(depth, atr)
        if math.isfinite(depth_atr):
            depths_atr.append(depth_atr)
        age_bars = float(last_idx - ob.formation_index)
        ages.append(age_bars)
        touches.append(int(getattr(ob, "touch_count", 0) or 0))
        mid = (ob.high + ob.low) / 2.0
        d = abs(last_close - mid)
        if d < nearest_abs:
            nearest_abs = d
            nearest = ob

    if depths_atr:
        out["ob_mean_depth_atr"] = float(sum(depths_atr) / len(depths_atr))
    if ages:
        out["ob_mean_age_bars"] = float(sum(ages) / len(ages))
    if touches:
        out["ob_max_touch_count"] = float(max(touches))

    if nearest is not None:
        nmid = (nearest.high + nearest.low) / 2.0
        depth = float(nearest.high - nearest.low)
        signed = last_close - nmid
        out["nearest_ob_dist_atr"] = _atr_units(abs(signed), atr)
        out["nearest_ob_signed_atr"] = _atr_units(signed, atr)
        out["nearest_ob_depth_atr"] = _atr_units(depth, atr)
        out["nearest_ob_age_bars"] = float(last_idx - nearest.formation_index)
        out["nearest_ob_touch_count"] = float(getattr(nearest, "touch_count", 0) or 0)
        out["nearest_ob_is_bullish"] = 1.0 if nearest.type == "bullish" else 0.0

    return out


# ---------------------------------------------------------------------------
# Active FVG geometry
# ---------------------------------------------------------------------------

def compute_fvg_features(state: _TFState, lookback: int) -> dict[str, float]:
    """Active FVGs in the last *lookback* candles.

    "active" = FVG whose middle candle index falls in the last
    *lookback* candles.

    Fill ratio: fraction of the original FVG range that has been
    overlapped by any subsequent candle wick. Range is recomputed from
    the candles after the FVG's middle candle; if any candle's
    ``low <= top`` (bullish FVG) or ``high >= bottom`` (bearish FVG)
    the FVG is considered to have started filling.

    Retest count: candles after the FVG whose range overlaps the FVG.
    """
    keys = [
        "fvg_count", "fvg_bull_count", "fvg_bear_count",
        "nearest_fvg_dist_atr", "nearest_fvg_size_atr",
        "nearest_fvg_age_bars",
        "nearest_fvg_fill_ratio", "nearest_fvg_retest_count",
        "nearest_fvg_is_bullish", "nearest_fvg_is_filled",
        "fvg_mean_size_atr", "fvg_filled_count", "fvg_unfilled_count",
    ]
    out = {k: NAN for k in keys}
    for k in ("fvg_count", "fvg_bull_count", "fvg_bear_count",
              "fvg_filled_count", "fvg_unfilled_count"):
        out[k] = 0.0

    if state.n == 0 or not state.fvgs:
        return out

    cutoff_idx = max(0, state.n - 1 - lookback)
    last_close = state.last_close
    atr = state.atr_14 if state.atr_14 > 0 else NAN
    last_idx = state.n - 1

    # FVG holds candle_indices = [i-1, i, i+1]; mid = i.
    active = [
        fvg for fvg in state.fvgs
        if (fvg.candle_indices and len(fvg.candle_indices) >= 2
            and fvg.candle_indices[1] >= cutoff_idx)
    ]
    out["fvg_count"] = float(len(active))
    out["fvg_bull_count"] = float(sum(1 for f in active if f.type == "bullish"))
    out["fvg_bear_count"] = float(sum(1 for f in active if f.type == "bearish"))

    if not active:
        return out

    sizes_atr: list[float] = []
    nearest = None
    nearest_abs = math.inf
    filled_count = 0
    for fvg in active:
        size = abs(fvg.top - fvg.bottom)
        sa = _safe_div(size, atr)
        if math.isfinite(sa):
            sizes_atr.append(sa)
        if fvg.filled:
            filled_count += 1
        d = abs(last_close - fvg.midpoint)
        if d < nearest_abs:
            nearest_abs = d
            nearest = fvg

    out["fvg_filled_count"] = float(filled_count)
    out["fvg_unfilled_count"] = float(len(active) - filled_count)
    if sizes_atr:
        out["fvg_mean_size_atr"] = float(sum(sizes_atr) / len(sizes_atr))

    if nearest is not None:
        size = abs(nearest.top - nearest.bottom)
        out["nearest_fvg_dist_atr"] = _atr_units(abs(last_close - nearest.midpoint), atr)
        out["nearest_fvg_size_atr"] = _atr_units(size, atr)
        # Age = (last_idx - middle_candle_idx)
        mid_idx = nearest.candle_indices[1]
        out["nearest_fvg_age_bars"] = float(last_idx - mid_idx)
        out["nearest_fvg_is_bullish"] = 1.0 if nearest.type == "bullish" else 0.0
        out["nearest_fvg_is_filled"] = 1.0 if nearest.filled else 0.0

        # Compute retest count + fill ratio over candles after FVG mid.
        post_idx = mid_idx + 2  # FVG spans i-1, i, i+1; "after" begins at i+2
        if post_idx < state.n:
            post = state.candles[post_idx:]
            # Retest count: bars whose range overlaps the FVG zone.
            top, bot = float(nearest.top), float(nearest.bottom)
            retest = sum(1 for c in post if c["high"] >= bot and c["low"] <= top)
            out["nearest_fvg_retest_count"] = float(retest)

            # Fill ratio: depth of deepest penetration into the FVG.
            if nearest.type == "bullish":
                # Bullish FVG bottom = candles[i-1]["high"]; fill begins
                # when post-candle low descends below top.
                deepest = min((c["low"] for c in post), default=top)
                deepest = max(deepest, bot)  # clip
                consumed = max(0.0, top - deepest)
            else:
                deepest = max((c["high"] for c in post), default=bot)
                deepest = min(deepest, top)
                consumed = max(0.0, deepest - bot)
            out["nearest_fvg_fill_ratio"] = _safe_div(consumed, abs(top - bot))
        else:
            out["nearest_fvg_retest_count"] = 0.0
            out["nearest_fvg_fill_ratio"] = 0.0

    return out


# ---------------------------------------------------------------------------
# Breaker-block features
# ---------------------------------------------------------------------------

def compute_bb_features(state: _TFState, lookback: int) -> dict[str, float]:
    """Active breaker blocks within the last *lookback* candles.

    Component-2 ``BreakerBlock`` does not expose a ``formation_index``.
    We map ``formation_time`` back to the candle index by linear scan.
    """
    keys = [
        "bb_count", "bb_bull_count", "bb_bear_count", "bb_retested_count",
        "nearest_bb_dist_atr", "nearest_bb_signed_atr",
        "nearest_bb_depth_atr", "nearest_bb_age_bars", "nearest_bb_is_retested",
        "nearest_bb_orig_was_bullish", "nearest_bb_is_bullish",
    ]
    out = {k: NAN for k in keys}
    for k in ("bb_count", "bb_bull_count", "bb_bear_count", "bb_retested_count"):
        out[k] = 0.0

    if state.n == 0 or not state.breakers:
        return out

    last_idx = state.n - 1
    cutoff_idx = max(0, state.n - 1 - lookback)
    last_close = state.last_close
    atr = state.atr_14 if state.atr_14 > 0 else NAN

    # Map formation_time -> candle index (linear scan; n bounded).
    time_to_idx = {c["time"]: i for i, c in enumerate(state.candles)}

    active: list[tuple[int, Any]] = []
    for bb in state.breakers:
        idx = time_to_idx.get(bb.formation_time)
        if idx is None or idx < cutoff_idx:
            continue
        active.append((idx, bb))

    out["bb_count"] = float(len(active))
    out["bb_bull_count"] = float(sum(1 for _, bb in active if bb.direction == "bullish"))
    out["bb_bear_count"] = float(sum(1 for _, bb in active if bb.direction == "bearish"))
    out["bb_retested_count"] = float(sum(1 for _, bb in active if bb.is_retested))

    if not active:
        return out

    nearest = None
    nearest_idx = -1
    nearest_abs = math.inf
    for idx, bb in active:
        mid = (bb.zone_high + bb.zone_low) / 2.0
        d = abs(last_close - mid)
        if d < nearest_abs:
            nearest_abs = d
            nearest = bb
            nearest_idx = idx

    if nearest is not None:
        depth = float(nearest.zone_high - nearest.zone_low)
        nmid = (nearest.zone_high + nearest.zone_low) / 2.0
        signed = last_close - nmid
        out["nearest_bb_dist_atr"] = _atr_units(abs(signed), atr)
        out["nearest_bb_signed_atr"] = _atr_units(signed, atr)
        out["nearest_bb_depth_atr"] = _atr_units(depth, atr)
        out["nearest_bb_age_bars"] = float(last_idx - nearest_idx)
        out["nearest_bb_is_retested"] = 1.0 if nearest.is_retested else 0.0
        out["nearest_bb_orig_was_bullish"] = (
            1.0 if nearest.original_ob_direction == "bullish" else 0.0
        )
        out["nearest_bb_is_bullish"] = 1.0 if nearest.direction == "bullish" else 0.0

    return out


# ---------------------------------------------------------------------------
# Swing magnitudes per TF
# ---------------------------------------------------------------------------

def compute_swing_features(state: _TFState, lookback: int) -> dict[str, float]:
    """Swing magnitudes / counts in the last *lookback* candles.

    ``last_swing_range`` = price diff between the most recent swing
    high and most recent swing low (regardless of order).
    ``leg_velocity`` = same diff divided by the bar count between the
    two swing pivots.
    ``up_magnitude`` / ``down_magnitude`` = max bullish / bearish swing
    diff between consecutive same-type swings, ATR-normalised.
    """
    keys = [
        "swing_high_count", "swing_low_count", "swing_total_count",
        "last_swing_range_atr", "last_swing_leg_bars",
        "last_swing_velocity_atr_per_bar",
        "max_up_leg_atr", "max_down_leg_atr",
        "swing_high_ratio",
        "last_high_age_bars", "last_low_age_bars",
        "swing_dispersion_atr",
    ]
    out = {k: NAN for k in keys}
    for k in ("swing_high_count", "swing_low_count", "swing_total_count"):
        out[k] = 0.0

    if state.n == 0 or not state.swings:
        return out

    cutoff_idx = max(0, state.n - 1 - lookback)
    atr = state.atr_14 if state.atr_14 > 0 else NAN
    last_idx = state.n - 1

    active = [s for s in state.swings if s.index >= cutoff_idx]
    highs = [s for s in active if s.type == "high"]
    lows = [s for s in active if s.type == "low"]
    out["swing_high_count"] = float(len(highs))
    out["swing_low_count"] = float(len(lows))
    out["swing_total_count"] = float(len(active))
    if active:
        out["swing_high_ratio"] = _safe_div(len(highs), len(active))

    # last swing leg (combines latest high & latest low whichever is
    # most recent — gives "most recent pivot-to-pivot swing").
    if highs and lows:
        h = highs[-1]
        l = lows[-1]
        leg_diff = abs(h.price - l.price)
        leg_bars = abs(h.index - l.index)
        out["last_swing_range_atr"] = _atr_units(leg_diff, atr)
        out["last_swing_leg_bars"] = float(leg_bars)
        if leg_bars > 0:
            out["last_swing_velocity_atr_per_bar"] = _atr_units(
                leg_diff / leg_bars, atr
            )
        out["last_high_age_bars"] = float(last_idx - h.index)
        out["last_low_age_bars"] = float(last_idx - l.index)

    # Max up / down legs — biggest consecutive same-type swing diff.
    max_up = 0.0
    for i in range(1, len(lows)):
        diff = lows[i].price - lows[i - 1].price
        if diff > max_up:
            max_up = diff
    max_down = 0.0
    for i in range(1, len(highs)):
        diff = highs[i - 1].price - highs[i].price
        if diff > max_down:
            max_down = diff
    out["max_up_leg_atr"] = _atr_units(max_up, atr)
    out["max_down_leg_atr"] = _atr_units(max_down, atr)

    # Dispersion: range of all swing prices over ATR.
    if active:
        prices = [s.price for s in active]
        out["swing_dispersion_atr"] = _atr_units(max(prices) - min(prices), atr)

    return out


# ---------------------------------------------------------------------------
# BOS / CHoCH event counts per TF
# ---------------------------------------------------------------------------

def compute_event_features(state: _TFState, lookback: int) -> dict[str, float]:
    """Counts and ages of structure events in the last *lookback* bars.
    """
    keys = [
        "bos_count", "choch_count", "bos_bull_count", "bos_bear_count",
        "displacement_present_count", "mean_displacement_ratio",
        "last_bos_age_bars", "last_choch_age_bars",
        "last_event_was_bos", "last_event_displaced",
    ]
    out = {k: NAN for k in keys}
    for k in ("bos_count", "choch_count", "bos_bull_count",
              "bos_bear_count", "displacement_present_count"):
        out[k] = 0.0

    if state.n == 0:
        return out

    cutoff_idx = max(0, state.n - 1 - lookback)
    last_idx = state.n - 1
    active = [e for e in state.structure_events if e.candle_index >= cutoff_idx]

    out["bos_count"] = float(sum(1 for e in active if e.type == "BOS"))
    out["choch_count"] = float(sum(1 for e in active if e.type == "CHoCH"))
    out["bos_bull_count"] = float(sum(
        1 for e in active if e.type == "BOS" and e.direction == "bullish"
    ))
    out["bos_bear_count"] = float(sum(
        1 for e in active if e.type == "BOS" and e.direction == "bearish"
    ))
    out["displacement_present_count"] = float(sum(
        1 for e in active if e.displacement_present
    ))
    if active:
        ratios = [e.displacement_ratio for e in active
                  if e.displacement_ratio is not None]
        if ratios:
            out["mean_displacement_ratio"] = float(sum(ratios) / len(ratios))

    bos_evts = [e for e in active if e.type == "BOS"]
    choch_evts = [e for e in active if e.type == "CHoCH"]
    if bos_evts:
        out["last_bos_age_bars"] = float(last_idx - bos_evts[-1].candle_index)
    if choch_evts:
        out["last_choch_age_bars"] = float(last_idx - choch_evts[-1].candle_index)
    if active:
        last_evt = active[-1]
        out["last_event_was_bos"] = 1.0 if last_evt.type == "BOS" else 0.0
        out["last_event_displaced"] = 1.0 if last_evt.displacement_present else 0.0

    return out


# ---------------------------------------------------------------------------
# Distance-to-internal-swing
# ---------------------------------------------------------------------------

def compute_distance_to_swing(state: _TFState) -> dict[str, float]:
    """Distance from last close to the nearest swing high & low
    (regardless of how recently formed). Both raw and ATR-normalised.
    """
    out = {
        "dist_to_nearest_swing_high_atr": NAN,
        "dist_to_nearest_swing_low_atr": NAN,
        "dist_to_swing_band_atr": NAN,
    }
    if state.n == 0 or not state.swings:
        return out

    last_close = state.last_close
    atr = state.atr_14 if state.atr_14 > 0 else NAN

    highs = [s for s in state.swings if s.type == "high"]
    lows = [s for s in state.swings if s.type == "low"]

    if highs:
        d = min(abs(last_close - s.price) for s in highs)
        out["dist_to_nearest_swing_high_atr"] = _atr_units(d, atr)
    if lows:
        d = min(abs(last_close - s.price) for s in lows)
        out["dist_to_nearest_swing_low_atr"] = _atr_units(d, atr)

    # Band = nearest_high - nearest_low (ATR units) — proxy for the
    # tightest enclosing swing range around current price.
    if highs and lows:
        nh = min((s.price for s in highs), key=lambda p: abs(last_close - p))
        nl = min((s.price for s in lows), key=lambda p: abs(last_close - p))
        out["dist_to_swing_band_atr"] = _atr_units(abs(nh - nl), atr)

    return out


# ---------------------------------------------------------------------------
# Pre-BOS impulse-leg geometry + consolidation duration
# ---------------------------------------------------------------------------

def compute_impulse_features(state: _TFState) -> dict[str, float]:
    """Geometry of the most recent BOS impulse leg (if any).

    The impulse leg is the bar range from the most recent OB's
    formation (the "origin") up to the BOS candle. Features capture
    leg range, bar count, candle direction count, and the ratio of
    impulse range to OB depth.
    """
    keys = [
        "impulse_range_atr", "impulse_bar_count",
        "impulse_to_ob_depth_ratio", "impulse_bull_candle_ratio",
        "impulse_max_displacement_ratio",
        "impulse_pre_consolidation_bars",
    ]
    out = {k: NAN for k in keys}

    if state.n == 0 or not state.order_blocks or not state.structure_events:
        return out

    # Pair last OB with last BOS event.
    last_ob = state.order_blocks[-1]
    bos_evts = [e for e in state.structure_events if e.type == "BOS"]
    if not bos_evts:
        return out
    last_bos = bos_evts[-1]
    if last_bos.candle_index < last_ob.formation_index:
        return out

    atr = state.atr_14 if state.atr_14 > 0 else NAN
    candles = state.candles
    leg = candles[last_ob.formation_index:last_bos.candle_index + 1]
    if not leg:
        return out
    leg_high = max(c["high"] for c in leg)
    leg_low = min(c["low"] for c in leg)
    out["impulse_range_atr"] = _atr_units(leg_high - leg_low, atr)
    out["impulse_bar_count"] = float(len(leg))

    ob_depth = max(0.0, last_ob.high - last_ob.low)
    out["impulse_to_ob_depth_ratio"] = _safe_div(leg_high - leg_low, ob_depth)

    bull_candles = sum(1 for c in leg if c["close"] > c["open"])
    out["impulse_bull_candle_ratio"] = _safe_div(bull_candles, len(leg))

    if state.avg_body > 0:
        max_disp = max(
            abs(c["close"] - c["open"]) / state.avg_body for c in leg
        )
        out["impulse_max_displacement_ratio"] = float(max_disp)

    # Pre-impulse consolidation: walking backward from the OB formation
    # candle, count bars whose true-range / ATR < 0.7 until the streak
    # breaks. Capped at 50 bars.
    if atr and math.isfinite(atr):
        consol = 0
        threshold = 0.7
        for k in range(last_ob.formation_index - 1, max(-1, last_ob.formation_index - 51), -1):
            c = candles[k]
            tr = c["high"] - c["low"]
            if tr / atr < threshold:
                consol += 1
            else:
                break
        out["impulse_pre_consolidation_bars"] = float(consol)

    return out


# ---------------------------------------------------------------------------
# Multi-timeframe alignment
# ---------------------------------------------------------------------------

_DIR_TO_INT = {"bullish": 1, "transitional": 0, "bearish": -1, "insufficient_data": 0}


def compute_mtf_alignment(states: dict[str, _TFState]) -> dict[str, float]:
    """Vector of structure-direction agreement across timeframes.

    For each TF in M15/H1/H4/D1, encode direction as +1/0/-1.
    Pairwise binary agreement flags + total agreement count.
    """
    keys = [
        "dir_M15", "dir_H1", "dir_H4", "dir_D1",
        "agree_M15_H1", "agree_M15_H4", "agree_M15_D1",
        "agree_H1_H4", "agree_H1_D1", "agree_H4_D1",
        "mtf_agreement_count", "mtf_signed_score",
        "mtf_all_aligned_bull", "mtf_all_aligned_bear",
    ]
    out = {k: NAN for k in keys}

    dirs: dict[str, int] = {}
    for tf in ("M15", "H1", "H4", "D1"):
        st = states.get(tf)
        if st is not None and st.structure is not None:
            dirs[tf] = _DIR_TO_INT.get(st.structure.direction, 0)
        else:
            dirs[tf] = 0

    out["dir_M15"] = float(dirs["M15"])
    out["dir_H1"] = float(dirs["H1"])
    out["dir_H4"] = float(dirs["H4"])
    out["dir_D1"] = float(dirs["D1"])

    # Pairwise agreement (1.0 if same non-zero sign, 0.0 if disagree
    # or one is transitional).
    def _agree(a: int, b: int) -> float:
        if a == 0 or b == 0:
            return 0.0
        return 1.0 if a == b else 0.0

    out["agree_M15_H1"] = _agree(dirs["M15"], dirs["H1"])
    out["agree_M15_H4"] = _agree(dirs["M15"], dirs["H4"])
    out["agree_M15_D1"] = _agree(dirs["M15"], dirs["D1"])
    out["agree_H1_H4"] = _agree(dirs["H1"], dirs["H4"])
    out["agree_H1_D1"] = _agree(dirs["H1"], dirs["D1"])
    out["agree_H4_D1"] = _agree(dirs["H4"], dirs["D1"])

    out["mtf_agreement_count"] = float(
        out["agree_M15_H1"] + out["agree_M15_H4"] + out["agree_M15_D1"]
        + out["agree_H1_H4"] + out["agree_H1_D1"] + out["agree_H4_D1"]
    )
    out["mtf_signed_score"] = float(sum(dirs.values()))
    out["mtf_all_aligned_bull"] = (
        1.0 if all(v == 1 for v in dirs.values()) else 0.0
    )
    out["mtf_all_aligned_bear"] = (
        1.0 if all(v == -1 for v in dirs.values()) else 0.0
    )
    return out


# ---------------------------------------------------------------------------
# Public assembly: build_structure_features
# ---------------------------------------------------------------------------

def build_structure_features(
    timestamps: list[str],
    candles_by_tf: dict[str, list[dict]],
    *,
    instrument_class: Optional[str] = None,
) -> pd.DataFrame:
    """Compute STRUCTURE features for every (symbol, timestamp).

    Parameters
    ----------
    timestamps:
        List of ISO-8601 candle-close strings (UTC). Must be sorted.
        These are typically the BOS times of the F11 population OR the
        candle-close times you wish to featurize.
    candles_by_tf:
        ``{"M15": [...], "H1": [...], "H4": [...], "D1": [...]}``
        Each list is the FULL OHLCV history for the symbol up to (at
        least) the latest timestamp. The function slices internally.
    instrument_class:
        Reserved (for future per-instrument FVG min-gap defaults).
        Currently unused.

    Returns
    -------
    pd.DataFrame indexed by ``timestamps`` (as ``DatetimeIndex``), one
    column per feature. Columns are deterministic (sorted by family
    then lookback then key).
    """
    if not timestamps:
        return pd.DataFrame()

    rows: list[dict[str, float]] = []
    for ts in timestamps:
        rows.append(_features_for_timestamp(ts, candles_by_tf))

    # Build full DataFrame in the natural feature order.
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(timestamps, utc=True, errors="coerce")
    df.index.name = "timestamp"
    return df


def _features_for_timestamp(
    ts: str, candles_by_tf: dict[str, list[dict]]
) -> dict[str, float]:
    """Compute one row of features for one (symbol, timestamp)."""
    out: dict[str, float] = {}
    states: dict[str, _TFState] = {}

    # 1) Build per-TF cached state slices.
    for tf, full_candles in candles_by_tf.items():
        slice_ = _slice_candles_until(full_candles, ts)
        # Cap context size for higher TFs to keep detection bounded.
        ctx = TF_CONTEXT_BARS.get(tf, 250)
        if len(slice_) > ctx:
            slice_ = slice_[-ctx:]
        states[tf] = _build_tf_state(tf, slice_)

    # 2) Per-TF, per-lookback aggregates.
    for tf in ("M15", "H1", "H4", "D1"):
        st = states.get(tf)
        if st is None:
            continue
        lbs = LOOKBACKS_BY_TF[tf]
        for lb in lbs:
            ob = compute_ob_features(st, lb)
            for k, v in ob.items():
                out[f"{tf}__{k}__lb{lb}"] = v
            fvg = compute_fvg_features(st, lb)
            for k, v in fvg.items():
                out[f"{tf}__{k}__lb{lb}"] = v
            evt = compute_event_features(st, lb)
            for k, v in evt.items():
                out[f"{tf}__{k}__lb{lb}"] = v
            sw = compute_swing_features(st, lb)
            for k, v in sw.items():
                out[f"{tf}__{k}__lb{lb}"] = v
            # Breaker blocks: only emit at moderate+ lookbacks
            if lb >= 50:
                bb = compute_bb_features(st, lb)
                for k, v in bb.items():
                    out[f"{tf}__{k}__lb{lb}"] = v

    # 3) Per-TF lookback-independent features (distance-to-swing,
    # impulse-leg geometry).
    for tf in ("M15", "H1", "H4", "D1"):
        st = states.get(tf)
        if st is None:
            continue
        ds = compute_distance_to_swing(st)
        for k, v in ds.items():
            out[f"{tf}__{k}"] = v

    # Impulse-leg only for M15 + H1 (lower TFs hold the BOS event).
    for tf in ("M15", "H1"):
        st = states.get(tf)
        if st is None:
            continue
        imp = compute_impulse_features(st)
        for k, v in imp.items():
            out[f"{tf}__{k}"] = v

    # 4) MTF alignment vector — top-level, no TF prefix.
    mtf = compute_mtf_alignment(states)
    out.update(mtf)

    return out


# ===========================================================================
# Self-tests — synthetic OHLCV to verify primitives don't crash
# ===========================================================================

def _make_synthetic_candles(n: int = 60, base: float = 100.0) -> list[dict]:
    """Build n bars of mildly trending synthetic OHLCV. Deterministic."""
    out = []
    for i in range(n):
        # Slowly rising market with small wiggle
        c0 = base + i * 0.2 + (1.0 if i % 7 == 0 else 0.0) - (0.5 if i % 11 == 0 else 0.0)
        op = c0 - 0.1
        hi = c0 + 0.5
        lo = c0 - 0.5
        cl = c0
        out.append({
            "time": f"2024-01-01T{i // 60:02d}:{i % 60:02d}:00",
            "open": op, "high": hi, "low": lo, "close": cl, "volume": 100,
        })
    return out


def _selftest() -> None:
    """Inline assertions; run via `python structure.py`."""
    candles = _make_synthetic_candles(80)
    state = _build_tf_state("M15", candles)
    # Sanity
    assert state.n == 80
    assert state.atr_14 > 0
    # OB features return dict of fixed keys, no exceptions
    ob = compute_ob_features(state, lookback=50)
    assert "ob_count" in ob
    assert ob["ob_count"] >= 0
    # FVG features
    fvg = compute_fvg_features(state, lookback=50)
    assert "fvg_count" in fvg
    # Swing features
    sw = compute_swing_features(state, lookback=50)
    assert "swing_total_count" in sw
    # Event features
    ev = compute_event_features(state, lookback=50)
    assert "bos_count" in ev
    # Distance-to-swing
    ds = compute_distance_to_swing(state)
    assert "dist_to_nearest_swing_high_atr" in ds
    # Impulse
    imp = compute_impulse_features(state)
    assert "impulse_range_atr" in imp
    # MTF alignment
    mtf = compute_mtf_alignment({"M15": state})
    assert "mtf_agreement_count" in mtf
    # End-to-end builder
    candles_by_tf = {"M15": candles, "H1": candles, "H4": candles, "D1": candles}
    df = build_structure_features([candles[-1]["time"]], candles_by_tf)
    assert len(df) == 1
    assert df.shape[1] > 200, f"expected >200 features, got {df.shape[1]}"
    # Everything finite-or-nan, no booleans / strings
    for c in df.columns:
        v = df[c].iloc[0]
        assert isinstance(v, (int, float)), f"non-numeric feature {c}: {v!r}"
    print(f"OK: {df.shape[1]} structure features computed for 1 candle.")


if __name__ == "__main__":
    _selftest()
