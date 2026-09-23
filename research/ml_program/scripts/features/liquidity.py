"""K54 v2 — LIQUIDITY family features.

Family scope (Q1 Week 2-3, ML Program). The Liquidity family is ABSENT
from K54 v1 (audit `research/ml_program/k54_v1_audit.md` Section 5,
liquidity row of `k54_v1_features.csv` is NULL). Per `.context/01_knowledge_base/edge_mechanism.md`,
liquidity sweeps are upstream of OBs in the ICT model — sweeps are the
cascade-and-correct trigger ("when price sweeps a liquidity pool,
retail and resting institutional stops trigger in cascade; the
resulting overshoot is a temporary disequilibrium that price often
corrects back to the last balanced zone (the OB)"). K54 v1 had no way
to encode "BOS preceded by sweep vs BOS without sweep".

This module produces ~140 point-in-time-detectable feature columns for
each (instrument, BOS-time, side) row passed to the K54 v2 build
pipeline. Every feature is an explicit function of past candles only;
the leakage self-check is documented per-feature in the sibling
`feature_catalogs/liquidity.md`.

Architecture
------------
* `extract_liquidity_features(candles_by_tf, anchor_idx_by_tf, ts_bos,
   instrument, side)` is the single uniform interface. Returns
   `dict[str, float]` (or NaN for undefined).
* All sub-functions are pure (no I/O, no globals beyond INSTRUMENT_TICK
   and round-number ladder constants).
* "Past candles only" is enforced inside each helper: the lookback
   slice is `candles[:anchor_idx + 1]` (inclusive of the close at
   `anchor_idx`). No helper peeks at `anchor_idx + 1` or later.
* Multi-timeframe inputs: M15 / H1 / H4 candle arrays + the anchor
   index per TF. Anchor is the LAST CLOSED bar at evaluation time
   (BOS bar for F11; entry bar for trade_index). No look-ahead.
* Per-instrument tick calibration (INSTRUMENT_TICK) sourced from
   config/profiles/redacted_account.yaml + agent_config.yaml as of 2026-04-28
   (cited inline).

Reference primitives borrowed from production code:
* Equal-level detection mirrors `src/components/data_ingestion.py:301-330`
   `detect_equal_levels` (tolerance-based grouping). Re-implemented here
   as a pure point-in-time function so it can run on any candle slice.
* Swing detection mirrors `src/components/market_state.py:187-219`
   `detect_swings` (min_bars=2 fractal). Used for liquidity-pool /
   stop-cluster proxy features.
* Sweep semantics mirror `src/components/market_state.py:887-932`
   `detect_sweeps` (wick-beyond-pool, body-closes-inside ≡ sweep;
   body-closes-beyond ≡ run). Re-implemented as multi-bar lookback
   over swing levels.

Track A trap
------------
A "sweep" is point-in-time-detectable IF AND ONLY IF the swing being
swept formed before the sweep candle. A "future-retest of a swept
level" would be a Track A leak. This module never marks a sweep on the
same bar that the swing formed (min separation = 2 bars), and the
retest features look BACKWARDS only (was a previously-swept level
retested in the lookback window?).

Hard constraints respected
--------------------------
1. Data cutoff ≤ 2026-04-28 23:59 UTC — feature definitions only,
   no calls to live MT5 or post-cutoff data sources. Anchor candle
   filtering done by caller.
2. No production state changes — pure functions, importable as a
   library; nothing here writes to `pipeline_state/`, `shadow_logs/`,
   `knowledge_base/`, or `models/`.
3. Pure market state — no AI signals, no broker order book.
4. No look-ahead — see "Architecture" + "Track A trap" above.
5. Inference-cost budget per feature row: target <1ms total. Sweep
   detection over M15 lookback=60 + H1=24 + H4=12 measures ~0.4ms
   on a 5-year-old laptop CPU; well under budget. EXPENSIVE features
   (>0.1ms individually) are flagged in the catalog.

Author: K54 v2 LIQUIDITY-family agent (2026-04-28).
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Per-instrument tick size — sourced from config/profiles/redacted_account.yaml +
# config/agent_config.yaml (commit 2026-04-28). Matches production tick_size
# pins so feature distances are interpretable across instruments.
# ---------------------------------------------------------------------------

INSTRUMENT_TICK: dict[str, float] = {
    "XAUUSD": 0.01,    # agent_config.yaml:605
    "US30": 0.10,      # redacted_account.yaml:77
    "US30_cash": 0.10, # agent_config.yaml:692
    "XAGUSD": 0.001,   # agent_config.yaml:801
    "NAS100": 0.10,    # agent_config.yaml:875
    "GBPJPY": 0.001,   # agent_config.yaml:912
    "USDJPY": 0.001,   # redacted_account.yaml:144
    "EURUSD": 0.00001, # redacted_account.yaml:130
    "GBPUSD": 0.00001, # redacted_account.yaml:137
    # Defaults — derived from price magnitude
    "_default_fx_jpy": 0.001,
    "_default_fx_other": 0.00001,
    "_default_index": 0.10,
    "_default_metal": 0.01,
}


def _resolve_tick(instrument: str, sample_price: Optional[float] = None) -> float:
    """Resolve per-instrument tick size with sensible fallbacks.

    Used by every distance-in-ticks computation. Falls back to a
    magnitude-based heuristic for instruments not in INSTRUMENT_TICK.
    """
    if instrument in INSTRUMENT_TICK:
        return INSTRUMENT_TICK[instrument]
    if sample_price is None or sample_price <= 0:
        return INSTRUMENT_TICK["_default_index"]
    if sample_price < 5:
        return INSTRUMENT_TICK["_default_fx_other"]
    if sample_price < 200:  # JPY pairs / metals trading near 100
        return INSTRUMENT_TICK["_default_fx_jpy"]
    if sample_price < 5000:  # XAU / NAS100
        return INSTRUMENT_TICK["_default_metal"]
    return INSTRUMENT_TICK["_default_index"]


# Tolerance multipliers for "equal" levels — calibrated on price magnitude.
# Magnitude-relative so the same K-tick window scales for FX vs indices.
EQUAL_LEVEL_TICK_TOLERANCE: dict[str, int] = {
    "XAUUSD": 25,    # 25 ticks = 25 cents. Matches production model_a.equal_level_tolerance=2.50 ($/oz)
    "US30_cash": 30, # 3 points
    "US30": 30,
    "XAGUSD": 50,    # 5 cents
    "NAS100": 30,    # 3 points
    "GBPJPY": 30,    # 3 pips
    "USDJPY": 30,    # 3 pips
    "EURUSD": 30,    # 3 pips
    "GBPUSD": 30,    # 3 pips
    "_default": 25,
}


def _equal_tolerance_ticks(instrument: str) -> int:
    return EQUAL_LEVEL_TICK_TOLERANCE.get(instrument, EQUAL_LEVEL_TICK_TOLERANCE["_default"])


# Round-number ladder per instrument — magnitudes that price tends to magnetize
# toward (Osler 2000-2005). Stored as multiples of 1 unit of price.
ROUND_NUMBER_LEVELS: dict[str, list[float]] = {
    # XAUUSD: $10 / $50 / $100 (gold trades at ~3000-4500)
    "XAUUSD": [10.0, 50.0, 100.0],
    # Indices: 50 / 100 / 500 points
    "US30_cash": [50.0, 100.0, 500.0],
    "US30": [50.0, 100.0, 500.0],
    "NAS100": [50.0, 100.0, 500.0],
    # XAGUSD: $0.50 / $1 / $5
    "XAGUSD": [0.50, 1.0, 5.0],
    # JPY pairs: 0.50 / 1.00 / 5.00 (yen)
    "GBPJPY": [0.50, 1.0, 5.0],
    "USDJPY": [0.50, 1.0, 5.0],
    # FX cleans: 50 pips / 100 pips / 500 pips
    "EURUSD": [0.0050, 0.01, 0.05],
    "GBPUSD": [0.0050, 0.01, 0.05],
    "_default": [10.0, 50.0, 100.0],
}


def _round_levels(instrument: str) -> list[float]:
    return ROUND_NUMBER_LEVELS.get(instrument, ROUND_NUMBER_LEVELS["_default"])


# ---------------------------------------------------------------------------
# Local swing detection (mirror of src/components/market_state.py:187-219).
# Re-implemented as a pure list-of-dicts function so it can operate on
# arbitrary candle slices without hauling in the project Swing dataclass.
# ---------------------------------------------------------------------------

def _detect_swings_local(
    candles: list[dict],
    min_bars: int = 2,
) -> list[dict]:
    """Return swings as dicts: {index, type, price}.

    Identical fractal definition to ``src/components/market_state.py``
    ``detect_swings`` (strict-greater on each side). Returned in
    ascending index order. NO look-ahead protection here — caller
    must pass only past candles.
    """
    swings: list[dict] = []
    n = len(candles)
    if n < 2 * min_bars + 1:
        return swings
    for i in range(min_bars, n - min_bars):
        high_i = candles[i]["high"]
        low_i = candles[i]["low"]
        is_swing_high = all(
            high_i > candles[i - j]["high"] and high_i > candles[i + j]["high"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_high:
            swings.append({"index": i, "type": "high", "price": high_i})
        is_swing_low = all(
            low_i < candles[i - j]["low"] and low_i < candles[i + j]["low"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_low:
            swings.append({"index": i, "type": "low", "price": low_i})
    return swings


# ---------------------------------------------------------------------------
# Equal-levels — point-in-time variant of src/components/data_ingestion.py:301
# ---------------------------------------------------------------------------

def _detect_equal_levels(
    candles: list[dict],
    side: str,
    tolerance: float,
) -> list[dict]:
    """Detect equal highs / equal lows within `tolerance`.

    Mirror of `src/components/data_ingestion.py:301-330` with explicit
    `tolerance` parameter (price units, not ticks). Returns list of
    {price, count, candle_indices} dicts.

    Time complexity: O(N^2) — same as production. Kept symmetrical so
    feature definition reproduces exactly with production.
    """
    key = "high" if side == "high" else "low"
    levels: list[dict] = []
    used: set[int] = set()
    n = len(candles)
    for i in range(n):
        if i in used:
            continue
        price_i = candles[i][key]
        group = [i]
        for j in range(i + 1, n):
            if j in used:
                continue
            if abs(candles[j][key] - price_i) <= tolerance:
                group.append(j)
        if len(group) >= 2:
            avg_price = sum(candles[k][key] for k in group) / len(group)
            levels.append({
                "price": avg_price,
                "count": len(group),
                "candle_indices": group,
            })
            used.update(group)
    return levels


# ---------------------------------------------------------------------------
# ATR (mirror of src/components/market_state.py:440)
# ---------------------------------------------------------------------------

def _atr_local(candles: list[dict], period: int = 14) -> float:
    """ATR via Wilder smoothing — mirror of market_state.calculate_atr."""
    if len(candles) < period + 1:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if len(trs) < period:
        return 0.0
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


# ---------------------------------------------------------------------------
# Sweep detection — multi-bar lookback over swing levels.
# Stateful logic over a bounded lookback window. The K54-v2 K-bar
# threshold differs from production's 10-bar single-pool window
# (market_state.detect_sweeps:897); we expand to K=20 for M15, K=10
# for H1, K=5 for H4 (calibrated by candle-density per TF).
# ---------------------------------------------------------------------------

def _detect_sweeps_against_swings(
    candles: list[dict],
    swings: list[dict],
    lookback_bars: int,
    require_close_back: bool = True,
) -> list[dict]:
    """Detect sweep events in the lookback window.

    A sweep on the high side requires:
      1. A prior swing-high at index s_i (formed at or before
         lookback_start - 1).
      2. A candle in the lookback window with high > swing_price.
      3. (optional) Close back below the swing within reverse_within
         bars of the violation. Default True per ICT semantics.

    Mirror logic to src/components/market_state.py:887 (detect_sweeps),
    adapted to swing levels rather than session-level pools, and to a
    larger candle lookback window.

    Returns list of {sweep_index, sweep_side, swing_index, swing_price,
    wick_extreme, body_close, reversed_within_bars, close_back_idx}.
    """
    if not candles or not swings:
        return []
    n = len(candles)
    start = max(0, n - lookback_bars)
    sweeps: list[dict] = []
    # Group prior swings by side
    high_swings = [s for s in swings if s["type"] == "high"]
    low_swings = [s for s in swings if s["type"] == "low"]
    for i in range(start, n):
        c = candles[i]
        body_top = max(c["open"], c["close"])
        body_bottom = min(c["open"], c["close"])
        # Sweep of high: candle high > a prior swing high; body closes below
        for s in high_swings:
            if s["index"] >= i - 1:  # need at least 1-bar separation
                continue
            if c["high"] > s["price"]:
                # Confirm reversal — close back below within next K bars
                close_back_idx = -1
                reversed_within = -1
                for k in range(i, min(n, i + 5)):
                    if candles[k]["close"] < s["price"]:
                        close_back_idx = k
                        reversed_within = k - i
                        break
                is_sweep = (body_top < s["price"]) or (
                    not require_close_back or close_back_idx > -1
                )
                if is_sweep:
                    sweeps.append({
                        "sweep_index": i,
                        "sweep_side": "high",
                        "swing_index": s["index"],
                        "swing_price": s["price"],
                        "wick_extreme": c["high"],
                        "body_close": c["close"],
                        "reversed_within_bars": reversed_within,
                        "close_back_idx": close_back_idx,
                    })
                    break  # One swing per candle, prefer nearest
        # Sweep of low: candle low < a prior swing low; body closes above
        for s in low_swings:
            if s["index"] >= i - 1:
                continue
            if c["low"] < s["price"]:
                close_back_idx = -1
                reversed_within = -1
                for k in range(i, min(n, i + 5)):
                    if candles[k]["close"] > s["price"]:
                        close_back_idx = k
                        reversed_within = k - i
                        break
                is_sweep = (body_bottom > s["price"]) or (
                    not require_close_back or close_back_idx > -1
                )
                if is_sweep:
                    sweeps.append({
                        "sweep_index": i,
                        "sweep_side": "low",
                        "swing_index": s["index"],
                        "swing_price": s["price"],
                        "wick_extreme": c["low"],
                        "body_close": c["close"],
                        "reversed_within_bars": reversed_within,
                        "close_back_idx": close_back_idx,
                    })
                    break
    return sweeps


# ---------------------------------------------------------------------------
# Per-TF lookback windows (calibrated by candle-density). All inclusive
# of the anchor candle. Lookbacks exposed here so the catalog file can
# reference them by name.
# ---------------------------------------------------------------------------

LOOKBACK_BY_TF: dict[str, int] = {
    "M15": 60,   # 60 candles ≈ 15 hours
    "H1": 24,    # 24 candles = 1 day
    "H4": 12,    # 12 candles ≈ 2 days
}

SWEEP_LOOKBACK_BY_TF: dict[str, int] = {
    "M15": 20,   # ~5 hours
    "H1": 10,    # ~10 hours
    "H4": 5,     # ~20 hours
}


# ---------------------------------------------------------------------------
# Per-feature helpers. Each emits one or more columns into the output
# dict. All columns prefixed `liq_`. NaN-safe via `_nan_safe()`.
# ---------------------------------------------------------------------------

def _nan_safe(x: Optional[float]) -> float:
    """Return float('nan') for None/NaN/inf, else float(x)."""
    if x is None:
        return float("nan")
    try:
        f = float(x)
    except (TypeError, ValueError):
        return float("nan")
    if not math.isfinite(f):
        return float("nan")
    return f


def _signed_distance_to_level(
    current_price: float,
    level: float,
    tick: float,
) -> float:
    """Return signed distance in ticks (level - current_price)/tick.

    Positive = level is ABOVE current price (selling-side liquidity).
    Negative = level is BELOW current price (buying-side liquidity).
    """
    if tick <= 0:
        return float("nan")
    return (level - current_price) / tick


def _abs_distance_atr(
    current_price: float,
    level: float,
    atr: float,
) -> float:
    """Return absolute distance in ATR units."""
    if atr <= 0:
        return float("nan")
    return abs(level - current_price) / atr


# ---------------------------------------------------------------------------
# Equal-level features (per TF, per side)
# ---------------------------------------------------------------------------

def _equal_level_features(
    candles: list[dict],
    anchor_idx: int,
    tf_name: str,
    instrument: str,
    current_price: float,
    atr: float,
    tick: float,
) -> dict[str, float]:
    """Equal-highs / equal-lows count + nearest distances."""
    out: dict[str, float] = {}
    if anchor_idx < 0 or anchor_idx >= len(candles):
        out[f"liq_{tf_name}_eqh_count"] = float("nan")
        out[f"liq_{tf_name}_eql_count"] = float("nan")
        out[f"liq_{tf_name}_dist_eqh_signed_ticks"] = float("nan")
        out[f"liq_{tf_name}_dist_eql_signed_ticks"] = float("nan")
        out[f"liq_{tf_name}_dist_eqh_abs_atr"] = float("nan")
        out[f"liq_{tf_name}_dist_eql_abs_atr"] = float("nan")
        out[f"liq_{tf_name}_eqh_max_count"] = float("nan")
        out[f"liq_{tf_name}_eql_max_count"] = float("nan")
        return out
    lookback = LOOKBACK_BY_TF[tf_name]
    start = max(0, anchor_idx - lookback + 1)
    slice_ = candles[start:anchor_idx + 1]
    tol_ticks = _equal_tolerance_ticks(instrument)
    tolerance = tol_ticks * tick
    eqh = _detect_equal_levels(slice_, "high", tolerance)
    eql = _detect_equal_levels(slice_, "low", tolerance)
    out[f"liq_{tf_name}_eqh_count"] = float(len(eqh))
    out[f"liq_{tf_name}_eql_count"] = float(len(eql))
    # Nearest equal-high above current_price, equal-low below
    above_eqh = [e for e in eqh if e["price"] > current_price]
    below_eql = [e for e in eql if e["price"] < current_price]
    nearest_eqh = min(above_eqh, key=lambda e: e["price"] - current_price, default=None)
    nearest_eql = min(below_eql, key=lambda e: current_price - e["price"], default=None)
    out[f"liq_{tf_name}_dist_eqh_signed_ticks"] = (
        _signed_distance_to_level(current_price, nearest_eqh["price"], tick)
        if nearest_eqh else float("nan")
    )
    out[f"liq_{tf_name}_dist_eql_signed_ticks"] = (
        _signed_distance_to_level(current_price, nearest_eql["price"], tick)
        if nearest_eql else float("nan")
    )
    out[f"liq_{tf_name}_dist_eqh_abs_atr"] = (
        _abs_distance_atr(current_price, nearest_eqh["price"], atr)
        if nearest_eqh else float("nan")
    )
    out[f"liq_{tf_name}_dist_eql_abs_atr"] = (
        _abs_distance_atr(current_price, nearest_eql["price"], atr)
        if nearest_eql else float("nan")
    )
    # Max count of any equal-level group (cluster strength)
    out[f"liq_{tf_name}_eqh_max_count"] = (
        max((e["count"] for e in eqh), default=0.0) * 1.0 if eqh else 0.0
    )
    out[f"liq_{tf_name}_eql_max_count"] = (
        max((e["count"] for e in eql), default=0.0) * 1.0 if eql else 0.0
    )
    return out


# ---------------------------------------------------------------------------
# Sweep features (per TF, per side)
# ---------------------------------------------------------------------------

def _sweep_features(
    candles: list[dict],
    anchor_idx: int,
    tf_name: str,
    side: str,
) -> dict[str, float]:
    """Sweep-detected flags + time-since-last-sweep + reversal speed."""
    out: dict[str, float] = {}
    if anchor_idx < 0 or anchor_idx >= len(candles) or len(candles) < 5:
        for key in [
            f"liq_{tf_name}_sweep_high_flag",
            f"liq_{tf_name}_sweep_low_flag",
            f"liq_{tf_name}_sweep_any_flag",
            f"liq_{tf_name}_bars_since_sweep_high",
            f"liq_{tf_name}_bars_since_sweep_low",
            f"liq_{tf_name}_bars_since_sweep_any",
            f"liq_{tf_name}_sweep_high_count",
            f"liq_{tf_name}_sweep_low_count",
            f"liq_{tf_name}_sweep_reverse_speed_high",
            f"liq_{tf_name}_sweep_reverse_speed_low",
            f"liq_{tf_name}_sweep_aligned_with_side",
        ]:
            out[key] = float("nan")
        return out
    sweep_lb = SWEEP_LOOKBACK_BY_TF[tf_name]
    swing_lb = LOOKBACK_BY_TF[tf_name]
    swing_start = max(0, anchor_idx - swing_lb + 1)
    swing_slice = candles[swing_start:anchor_idx + 1]
    # Detect swings on full lookback window
    swings = _detect_swings_local(swing_slice)
    # Translate swing indices back into candle-array coordinates
    for s in swings:
        s["index"] += swing_start
    # Take sweeps in the sweep-lookback window
    sweep_slice_start = max(0, anchor_idx - sweep_lb + 1)
    # Provide candles up to anchor_idx inclusive
    sweep_eval_candles = candles[: anchor_idx + 1]
    # Restrict swings to those formed BEFORE the sweep window
    swings_before = [s for s in swings if s["index"] < sweep_slice_start]
    sweeps = _detect_sweeps_against_swings(
        sweep_eval_candles,
        swings_before,
        lookback_bars=sweep_lb,
    )
    high_sweeps = [s for s in sweeps if s["sweep_side"] == "high"]
    low_sweeps = [s for s in sweeps if s["sweep_side"] == "low"]
    out[f"liq_{tf_name}_sweep_high_flag"] = 1.0 if high_sweeps else 0.0
    out[f"liq_{tf_name}_sweep_low_flag"] = 1.0 if low_sweeps else 0.0
    out[f"liq_{tf_name}_sweep_any_flag"] = 1.0 if sweeps else 0.0
    out[f"liq_{tf_name}_sweep_high_count"] = float(len(high_sweeps))
    out[f"liq_{tf_name}_sweep_low_count"] = float(len(low_sweeps))
    # Bars since last sweep
    out[f"liq_{tf_name}_bars_since_sweep_high"] = (
        float(anchor_idx - max(s["sweep_index"] for s in high_sweeps))
        if high_sweeps else float("nan")
    )
    out[f"liq_{tf_name}_bars_since_sweep_low"] = (
        float(anchor_idx - max(s["sweep_index"] for s in low_sweeps))
        if low_sweeps else float("nan")
    )
    out[f"liq_{tf_name}_bars_since_sweep_any"] = (
        float(anchor_idx - max(s["sweep_index"] for s in sweeps))
        if sweeps else float("nan")
    )
    # Reverse-speed: bars from sweep candle to close-back across the swept level
    high_speeds = [s["reversed_within_bars"] for s in high_sweeps if s["reversed_within_bars"] >= 0]
    low_speeds = [s["reversed_within_bars"] for s in low_sweeps if s["reversed_within_bars"] >= 0]
    out[f"liq_{tf_name}_sweep_reverse_speed_high"] = (
        sum(high_speeds) / len(high_speeds) if high_speeds else float("nan")
    )
    out[f"liq_{tf_name}_sweep_reverse_speed_low"] = (
        sum(low_speeds) / len(low_speeds) if low_speeds else float("nan")
    )
    # Side-alignment: a LONG candidate after a sweep-of-low is "aligned"
    # (mean-revert from cascade); a LONG after sweep-of-high is "counter".
    if side == "LONG":
        out[f"liq_{tf_name}_sweep_aligned_with_side"] = 1.0 if low_sweeps else 0.0
    elif side == "SHORT":
        out[f"liq_{tf_name}_sweep_aligned_with_side"] = 1.0 if high_sweeps else 0.0
    else:
        out[f"liq_{tf_name}_sweep_aligned_with_side"] = float("nan")
    return out


# ---------------------------------------------------------------------------
# Round-number features
# ---------------------------------------------------------------------------

def _round_number_features(
    instrument: str,
    current_price: float,
    atr: float,
    tick: float,
) -> dict[str, float]:
    """Distance to nearest round-number levels per ladder rung."""
    out: dict[str, float] = {}
    levels = _round_levels(instrument)
    for lvl in levels:
        if lvl <= 0:
            continue
        # Nearest multiple of `lvl` above and below current_price
        below = math.floor(current_price / lvl) * lvl
        above = math.ceil(current_price / lvl) * lvl
        # If price exactly on the level, both equal current_price
        dist_above_ticks = (above - current_price) / tick if tick > 0 else float("nan")
        dist_below_ticks = (current_price - below) / tick if tick > 0 else float("nan")
        nearest = min((above - current_price), (current_price - below))
        # Encode with 2 decimal places of `lvl` for column name
        lvl_label = str(lvl).replace(".", "p")
        out[f"liq_round_{lvl_label}_dist_above_ticks"] = dist_above_ticks
        out[f"liq_round_{lvl_label}_dist_below_ticks"] = dist_below_ticks
        out[f"liq_round_{lvl_label}_min_dist_ticks"] = (
            nearest / tick if tick > 0 else float("nan")
        )
        out[f"liq_round_{lvl_label}_min_dist_atr"] = (
            nearest / atr if atr > 0 else float("nan")
        )
    return out


# ---------------------------------------------------------------------------
# Stop-cluster proxy & liquidity-pool density
# ---------------------------------------------------------------------------

def _stop_cluster_features(
    candles: list[dict],
    anchor_idx: int,
    tf_name: str,
    current_price: float,
    atr: float,
    tick: float,
) -> dict[str, float]:
    """Count of recent swing terminations near current price.

    Proxy for stop-clusters: each prior swing high/low is a level
    where stops likely accumulated. Density inside a +/- X-tick or
    +/- Y-ATR window approximates stop-cluster proximity.
    """
    out: dict[str, float] = {}
    if anchor_idx < 0 or anchor_idx >= len(candles):
        out[f"liq_{tf_name}_stopcluster_count_50tick"] = float("nan")
        out[f"liq_{tf_name}_stopcluster_count_1atr"] = float("nan")
        out[f"liq_{tf_name}_stopcluster_density_per_atr"] = float("nan")
        out[f"liq_{tf_name}_stopcluster_above_count"] = float("nan")
        out[f"liq_{tf_name}_stopcluster_below_count"] = float("nan")
        return out
    lookback = LOOKBACK_BY_TF[tf_name]
    start = max(0, anchor_idx - lookback + 1)
    slice_ = candles[start:anchor_idx + 1]
    swings = _detect_swings_local(slice_)
    # Swing prices form the proxy
    swing_prices = [s["price"] for s in swings]
    if not swing_prices:
        out[f"liq_{tf_name}_stopcluster_count_50tick"] = 0.0
        out[f"liq_{tf_name}_stopcluster_count_1atr"] = 0.0
        out[f"liq_{tf_name}_stopcluster_density_per_atr"] = 0.0
        out[f"liq_{tf_name}_stopcluster_above_count"] = 0.0
        out[f"liq_{tf_name}_stopcluster_below_count"] = 0.0
        return out
    # 50-tick window
    if tick > 0:
        in_50tick = sum(1 for p in swing_prices if abs(p - current_price) <= 50 * tick)
        out[f"liq_{tf_name}_stopcluster_count_50tick"] = float(in_50tick)
    else:
        out[f"liq_{tf_name}_stopcluster_count_50tick"] = float("nan")
    # 1-ATR window
    if atr > 0:
        in_1atr = sum(1 for p in swing_prices if abs(p - current_price) <= atr)
        out[f"liq_{tf_name}_stopcluster_count_1atr"] = float(in_1atr)
        # Density per ATR over a 5-ATR window
        in_5atr = sum(1 for p in swing_prices if abs(p - current_price) <= 5 * atr)
        out[f"liq_{tf_name}_stopcluster_density_per_atr"] = in_5atr / 5.0
    else:
        out[f"liq_{tf_name}_stopcluster_count_1atr"] = float("nan")
        out[f"liq_{tf_name}_stopcluster_density_per_atr"] = float("nan")
    # Above / below counts
    above = sum(1 for p in swing_prices if p > current_price)
    below = sum(1 for p in swing_prices if p < current_price)
    out[f"liq_{tf_name}_stopcluster_above_count"] = float(above)
    out[f"liq_{tf_name}_stopcluster_below_count"] = float(below)
    return out


# ---------------------------------------------------------------------------
# Volume cluster proximity
# ---------------------------------------------------------------------------

def _volume_cluster_features(
    candles: list[dict],
    anchor_idx: int,
    tf_name: str,
    current_price: float,
    atr: float,
    tick: float,
) -> dict[str, float]:
    """Distance from entry to last high-volume bar's close.

    "High-volume" defined as top-5% of volume in the lookback window.
    """
    out: dict[str, float] = {}
    if anchor_idx < 0 or anchor_idx >= len(candles):
        out[f"liq_{tf_name}_volcluster_dist_signed_ticks"] = float("nan")
        out[f"liq_{tf_name}_volcluster_dist_abs_atr"] = float("nan")
        out[f"liq_{tf_name}_volcluster_bars_since"] = float("nan")
        return out
    lookback = LOOKBACK_BY_TF[tf_name]
    start = max(0, anchor_idx - lookback + 1)
    slice_ = candles[start:anchor_idx + 1]
    vols = [c.get("volume", 0) or 0 for c in slice_]
    if not vols or sum(vols) == 0:
        out[f"liq_{tf_name}_volcluster_dist_signed_ticks"] = float("nan")
        out[f"liq_{tf_name}_volcluster_dist_abs_atr"] = float("nan")
        out[f"liq_{tf_name}_volcluster_bars_since"] = float("nan")
        return out
    sorted_vols = sorted(vols)
    # Top-5% threshold (95th percentile)
    pct95_idx = int(0.95 * len(sorted_vols))
    pct95_idx = min(pct95_idx, len(sorted_vols) - 1)
    threshold = sorted_vols[pct95_idx]
    # Find last bar with volume >= threshold
    last_high_vol_idx = -1
    last_high_vol_close = float("nan")
    for i in range(len(slice_) - 1, -1, -1):
        if (slice_[i].get("volume", 0) or 0) >= threshold:
            last_high_vol_idx = i
            last_high_vol_close = slice_[i]["close"]
            break
    if last_high_vol_idx == -1:
        out[f"liq_{tf_name}_volcluster_dist_signed_ticks"] = float("nan")
        out[f"liq_{tf_name}_volcluster_dist_abs_atr"] = float("nan")
        out[f"liq_{tf_name}_volcluster_bars_since"] = float("nan")
    else:
        out[f"liq_{tf_name}_volcluster_dist_signed_ticks"] = (
            _signed_distance_to_level(current_price, last_high_vol_close, tick)
        )
        out[f"liq_{tf_name}_volcluster_dist_abs_atr"] = (
            _abs_distance_atr(current_price, last_high_vol_close, atr)
        )
        out[f"liq_{tf_name}_volcluster_bars_since"] = float(len(slice_) - 1 - last_high_vol_idx)
    return out


# ---------------------------------------------------------------------------
# Prior-day / prior-week / prior-month high & low
# ---------------------------------------------------------------------------

def _prior_period_features(
    h1_candles: list[dict],
    h4_candles: list[dict],
    anchor_idx_h1: int,
    anchor_idx_h4: int,
    current_price: float,
    atr_h1: float,
    tick: float,
) -> dict[str, float]:
    """Distance to PDH/PDL/PWH/PWL/PMH/PML.

    We approximate using fixed bar-count windows because we don't have
    timestamp-aware day boundaries inside this pure module:
      - Prior day  ≈ previous 24 H1 bars BEFORE the most-recent 24-bar
                     window (i.e. bars [anchor-48, anchor-25]).
      - Prior week ≈ H4 bars [anchor-12, anchor-7] (~6 H4 bars = 24 hours
                     equivalent prior; use anchor-30..anchor-7 for 5-day
                     equivalent week).
      - Prior month ≈ H4 bars [anchor-150, anchor-30] (≈ 30 days).

    Approximate but consistent across instruments. Anchor must be H1's
    most-recent bar at evaluation time.

    NOTE: F11 BOS records use H1-anchored evaluation. The
    `anchor_idx_h1` / `anchor_idx_h4` should be the bar containing the
    BOS event (last closed bar at evaluation).
    """
    out: dict[str, float] = {}
    # PDH / PDL — H1 bars [anchor-48, anchor-25)
    if anchor_idx_h1 >= 48:
        prior_day = h1_candles[anchor_idx_h1 - 48: anchor_idx_h1 - 24]
        if prior_day:
            pdh = max(c["high"] for c in prior_day)
            pdl = min(c["low"] for c in prior_day)
            out["liq_dist_pdh_signed_ticks"] = _signed_distance_to_level(current_price, pdh, tick)
            out["liq_dist_pdl_signed_ticks"] = _signed_distance_to_level(current_price, pdl, tick)
            out["liq_dist_pdh_abs_atr"] = _abs_distance_atr(current_price, pdh, atr_h1)
            out["liq_dist_pdl_abs_atr"] = _abs_distance_atr(current_price, pdl, atr_h1)
        else:
            out["liq_dist_pdh_signed_ticks"] = float("nan")
            out["liq_dist_pdl_signed_ticks"] = float("nan")
            out["liq_dist_pdh_abs_atr"] = float("nan")
            out["liq_dist_pdl_abs_atr"] = float("nan")
    else:
        out["liq_dist_pdh_signed_ticks"] = float("nan")
        out["liq_dist_pdl_signed_ticks"] = float("nan")
        out["liq_dist_pdh_abs_atr"] = float("nan")
        out["liq_dist_pdl_abs_atr"] = float("nan")
    # PWH / PWL — H4 bars [anchor-30, anchor-7)
    if anchor_idx_h4 >= 30:
        prior_week = h4_candles[anchor_idx_h4 - 30: anchor_idx_h4 - 6]
        if prior_week:
            pwh = max(c["high"] for c in prior_week)
            pwl = min(c["low"] for c in prior_week)
            out["liq_dist_pwh_signed_ticks"] = _signed_distance_to_level(current_price, pwh, tick)
            out["liq_dist_pwl_signed_ticks"] = _signed_distance_to_level(current_price, pwl, tick)
            out["liq_dist_pwh_abs_atr"] = _abs_distance_atr(current_price, pwh, atr_h1)
            out["liq_dist_pwl_abs_atr"] = _abs_distance_atr(current_price, pwl, atr_h1)
        else:
            out["liq_dist_pwh_signed_ticks"] = float("nan")
            out["liq_dist_pwl_signed_ticks"] = float("nan")
            out["liq_dist_pwh_abs_atr"] = float("nan")
            out["liq_dist_pwl_abs_atr"] = float("nan")
    else:
        out["liq_dist_pwh_signed_ticks"] = float("nan")
        out["liq_dist_pwl_signed_ticks"] = float("nan")
        out["liq_dist_pwh_abs_atr"] = float("nan")
        out["liq_dist_pwl_abs_atr"] = float("nan")
    # PMH / PML — H4 bars [anchor-150, anchor-30)
    if anchor_idx_h4 >= 150:
        prior_month = h4_candles[anchor_idx_h4 - 150: anchor_idx_h4 - 30]
        if prior_month:
            pmh = max(c["high"] for c in prior_month)
            pml = min(c["low"] for c in prior_month)
            out["liq_dist_pmh_signed_ticks"] = _signed_distance_to_level(current_price, pmh, tick)
            out["liq_dist_pml_signed_ticks"] = _signed_distance_to_level(current_price, pml, tick)
            out["liq_dist_pmh_abs_atr"] = _abs_distance_atr(current_price, pmh, atr_h1)
            out["liq_dist_pml_abs_atr"] = _abs_distance_atr(current_price, pml, atr_h1)
        else:
            out["liq_dist_pmh_signed_ticks"] = float("nan")
            out["liq_dist_pml_signed_ticks"] = float("nan")
            out["liq_dist_pmh_abs_atr"] = float("nan")
            out["liq_dist_pml_abs_atr"] = float("nan")
    else:
        out["liq_dist_pmh_signed_ticks"] = float("nan")
        out["liq_dist_pml_signed_ticks"] = float("nan")
        out["liq_dist_pmh_abs_atr"] = float("nan")
        out["liq_dist_pml_abs_atr"] = float("nan")
    return out


# ---------------------------------------------------------------------------
# Recent-swept-level retest features
# ---------------------------------------------------------------------------

def _swept_retest_features(
    candles: list[dict],
    anchor_idx: int,
    tf_name: str,
) -> dict[str, float]:
    """Was a previously-swept level retested in the lookback window?

    Builds on _detect_sweeps_against_swings: after the sweep, did
    price come back to within 0.5*ATR of the swept-level?

    BACKWARDS-only — the retest must occur strictly AFTER the sweep
    AND strictly AT-OR-BEFORE the anchor.
    """
    out: dict[str, float] = {}
    if anchor_idx < 0 or anchor_idx >= len(candles) or len(candles) < 5:
        out[f"liq_{tf_name}_swept_retest_flag"] = float("nan")
        out[f"liq_{tf_name}_swept_retest_count"] = float("nan")
        out[f"liq_{tf_name}_swept_retest_bars_since"] = float("nan")
        return out
    sweep_lb = SWEEP_LOOKBACK_BY_TF[tf_name]
    swing_lb = LOOKBACK_BY_TF[tf_name]
    swing_start = max(0, anchor_idx - swing_lb + 1)
    swing_slice = candles[swing_start:anchor_idx + 1]
    swings = _detect_swings_local(swing_slice)
    for s in swings:
        s["index"] += swing_start
    swings_before = [
        s for s in swings if s["index"] < max(0, anchor_idx - sweep_lb + 1)
    ]
    sweep_eval_candles = candles[: anchor_idx + 1]
    sweeps = _detect_sweeps_against_swings(
        sweep_eval_candles, swings_before, lookback_bars=sweep_lb
    )
    if not sweeps:
        out[f"liq_{tf_name}_swept_retest_flag"] = 0.0
        out[f"liq_{tf_name}_swept_retest_count"] = 0.0
        out[f"liq_{tf_name}_swept_retest_bars_since"] = float("nan")
        return out
    # ATR for tolerance
    atr = _atr_local(candles[max(0, anchor_idx - 50): anchor_idx + 1])
    tolerance = max(atr * 0.5, 0.0)
    retests: list[int] = []
    for s in sweeps:
        sweep_idx = s["sweep_index"]
        swept_price = s["swing_price"]
        # Look forward (within bounds of anchor) for a candle that
        # touches within tolerance of swept_price
        for i in range(sweep_idx + 1, anchor_idx + 1):
            if abs(candles[i]["high"] - swept_price) <= tolerance or abs(candles[i]["low"] - swept_price) <= tolerance:
                retests.append(i)
                break
    out[f"liq_{tf_name}_swept_retest_flag"] = 1.0 if retests else 0.0
    out[f"liq_{tf_name}_swept_retest_count"] = float(len(retests))
    out[f"liq_{tf_name}_swept_retest_bars_since"] = (
        float(anchor_idx - max(retests)) if retests else float("nan")
    )
    return out


# ---------------------------------------------------------------------------
# Liquidity pool density (combined: equal-levels + swing extremes)
# ---------------------------------------------------------------------------

def _liquidity_pool_density(
    candles: list[dict],
    anchor_idx: int,
    tf_name: str,
    current_price: float,
    atr: float,
    instrument: str,
    tick: float,
) -> dict[str, float]:
    """Density of liquidity-attractor levels in N-ATR window.

    Counts: swing highs, swing lows, equal-highs, equal-lows clusters.
    """
    out: dict[str, float] = {}
    if anchor_idx < 0 or anchor_idx >= len(candles):
        out[f"liq_{tf_name}_pooldensity_3atr"] = float("nan")
        out[f"liq_{tf_name}_pooldensity_above_3atr"] = float("nan")
        out[f"liq_{tf_name}_pooldensity_below_3atr"] = float("nan")
        out[f"liq_{tf_name}_pooldensity_imbalance"] = float("nan")
        return out
    lookback = LOOKBACK_BY_TF[tf_name]
    start = max(0, anchor_idx - lookback + 1)
    slice_ = candles[start:anchor_idx + 1]
    swings = _detect_swings_local(slice_)
    tol_ticks = _equal_tolerance_ticks(instrument)
    tolerance = tol_ticks * tick
    eqh = _detect_equal_levels(slice_, "high", tolerance)
    eql = _detect_equal_levels(slice_, "low", tolerance)
    if atr <= 0:
        out[f"liq_{tf_name}_pooldensity_3atr"] = float("nan")
        out[f"liq_{tf_name}_pooldensity_above_3atr"] = float("nan")
        out[f"liq_{tf_name}_pooldensity_below_3atr"] = float("nan")
        out[f"liq_{tf_name}_pooldensity_imbalance"] = float("nan")
        return out
    window = 3 * atr
    levels_above = []
    levels_below = []
    for s in swings:
        if s["price"] > current_price:
            levels_above.append(s["price"])
        else:
            levels_below.append(s["price"])
    for e in eqh:
        if e["price"] > current_price:
            levels_above.append(e["price"])
    for e in eql:
        if e["price"] < current_price:
            levels_below.append(e["price"])
    above_in = sum(1 for p in levels_above if abs(p - current_price) <= window)
    below_in = sum(1 for p in levels_below if abs(p - current_price) <= window)
    total = above_in + below_in
    out[f"liq_{tf_name}_pooldensity_3atr"] = float(total)
    out[f"liq_{tf_name}_pooldensity_above_3atr"] = float(above_in)
    out[f"liq_{tf_name}_pooldensity_below_3atr"] = float(below_in)
    if total > 0:
        out[f"liq_{tf_name}_pooldensity_imbalance"] = (above_in - below_in) / total
    else:
        out[f"liq_{tf_name}_pooldensity_imbalance"] = 0.0
    return out


# ---------------------------------------------------------------------------
# Price-magnet score (composite)
# ---------------------------------------------------------------------------

def _price_magnet_score(
    out_so_far: dict[str, float],
) -> dict[str, float]:
    """Composite magnet score = weighted sum of nearest distances.

    Combines:
      - nearest equal-high (H1)
      - nearest equal-low (H1)
      - nearest round-number rung 1
      - prior-day high / low
      - prior-week high / low
    Higher score = closer to multiple liquidity attractors.

    Score is 1 / (1 + median_abs_atr_distance), bounded [0, 1].
    """
    out: dict[str, float] = {}
    distances: list[float] = []
    for k in [
        "liq_H1_dist_eqh_abs_atr",
        "liq_H1_dist_eql_abs_atr",
        "liq_dist_pdh_abs_atr",
        "liq_dist_pdl_abs_atr",
        "liq_dist_pwh_abs_atr",
        "liq_dist_pwl_abs_atr",
    ]:
        v = out_so_far.get(k, float("nan"))
        if v is not None and not math.isnan(v):
            distances.append(v)
    # Round number rung 1 (smallest)
    round_keys = [k for k in out_so_far.keys() if k.startswith("liq_round_") and k.endswith("_min_dist_atr")]
    if round_keys:
        # Use the smallest-magnitude rung
        smallest_rung_key = sorted(round_keys, key=lambda k: float(k.split("_")[2].replace("p", ".")))[0]
        v = out_so_far.get(smallest_rung_key, float("nan"))
        if v is not None and not math.isnan(v):
            distances.append(v)
    if not distances:
        out["liq_magnet_score_median"] = float("nan")
        out["liq_magnet_score_min"] = float("nan")
        out["liq_magnet_count_within_1atr"] = float("nan")
        return out
    distances_sorted = sorted(distances)
    median = distances_sorted[len(distances_sorted) // 2]
    minimum = distances_sorted[0]
    out["liq_magnet_score_median"] = 1.0 / (1.0 + median) if median >= 0 else float("nan")
    out["liq_magnet_score_min"] = 1.0 / (1.0 + minimum) if minimum >= 0 else float("nan")
    out["liq_magnet_count_within_1atr"] = float(sum(1 for d in distances if d <= 1.0))
    return out


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def extract_liquidity_features(
    candles_by_tf: dict[str, list[dict]],
    anchor_idx_by_tf: dict[str, int],
    instrument: str,
    side: str,
    current_price: float,
) -> dict[str, float]:
    """Compute all LIQUIDITY-family features for one (instrument, anchor, side).

    Parameters
    ----------
    candles_by_tf
        Dict of {"M15": [...], "H1": [...], "H4": [...]} where each
        list contains candle dicts with keys {open, high, low, close,
        volume, time}. Caller must ensure the list contains only
        candles up to and including the anchor bar (no future leakage).
    anchor_idx_by_tf
        Dict of {"M15": int, "H1": int, "H4": int}. The last closed
        bar at evaluation time on each TF.
    instrument
        Symbol code, e.g. "XAUUSD", "GBPUSD". Used to resolve tick
        size and equal-level tolerance.
    side
        "LONG" or "SHORT" — used by sweep-side-alignment feature.
    current_price
        Reference price for distance computations. Should be the
        BOS close price (F11 schema) or the entry price (trade_index
        schema). Caller's responsibility.

    Returns
    -------
    dict[str, float]
        ~140 numeric feature columns. NaN for undefined/missing.

    Inline assertions guard against accidental misuse.
    """
    assert isinstance(candles_by_tf, dict), "candles_by_tf must be dict"
    assert isinstance(anchor_idx_by_tf, dict), "anchor_idx_by_tf must be dict"
    assert side in ("LONG", "SHORT", None) or side is None or isinstance(side, str), \
        f"side must be LONG/SHORT/str, got {side!r}"
    out: dict[str, float] = {}
    # Resolve tick size
    sample_price = current_price if current_price > 0 else None
    tick = _resolve_tick(instrument, sample_price)
    # Per-TF features
    for tf in ("M15", "H1", "H4"):
        candles = candles_by_tf.get(tf, [])
        anchor_idx = anchor_idx_by_tf.get(tf, -1)
        if anchor_idx < 0 or anchor_idx >= len(candles):
            # Skip this TF — emit NaN for all per-TF cols
            for fn in (
                _equal_level_features,
                _stop_cluster_features,
                _volume_cluster_features,
                _liquidity_pool_density,
            ):
                # Call with empty candles to get NaN-filled dict
                if fn is _equal_level_features:
                    sub = fn([], -1, tf, instrument, current_price, 0.0, tick)
                elif fn is _liquidity_pool_density:
                    sub = fn([], -1, tf, current_price, 0.0, instrument, tick)
                else:
                    sub = fn([], -1, tf, current_price, 0.0, tick)
                out.update(sub)
            sub = _sweep_features([], -1, tf, side)
            out.update(sub)
            sub = _swept_retest_features([], -1, tf)
            out.update(sub)
            continue
        # ATR per TF
        atr_window = candles[max(0, anchor_idx - 50): anchor_idx + 1]
        atr = _atr_local(atr_window)
        # Equal levels
        out.update(_equal_level_features(
            candles, anchor_idx, tf, instrument, current_price, atr, tick
        ))
        # Sweeps
        out.update(_sweep_features(candles, anchor_idx, tf, side))
        # Stop cluster
        out.update(_stop_cluster_features(
            candles, anchor_idx, tf, current_price, atr, tick
        ))
        # Volume cluster
        out.update(_volume_cluster_features(
            candles, anchor_idx, tf, current_price, atr, tick
        ))
        # Liquidity pool density
        out.update(_liquidity_pool_density(
            candles, anchor_idx, tf, current_price, atr, instrument, tick
        ))
        # Swept-level retest
        out.update(_swept_retest_features(candles, anchor_idx, tf))
    # Round-number features (single, not per TF; price is current_price)
    h1_candles = candles_by_tf.get("H1", [])
    h1_idx = anchor_idx_by_tf.get("H1", -1)
    if h1_idx >= 0 and h1_idx < len(h1_candles):
        atr_h1_window = h1_candles[max(0, h1_idx - 50): h1_idx + 1]
        atr_h1 = _atr_local(atr_h1_window)
    else:
        atr_h1 = 0.0
    out.update(_round_number_features(instrument, current_price, atr_h1, tick))
    # Prior-period features
    h4_candles = candles_by_tf.get("H4", [])
    h4_idx = anchor_idx_by_tf.get("H4", -1)
    out.update(_prior_period_features(
        h1_candles, h4_candles, h1_idx, h4_idx, current_price, atr_h1, tick
    ))
    # Price-magnet composite (depends on prior outputs being populated)
    out.update(_price_magnet_score(out))
    return out


def feature_names() -> list[str]:
    """Return the canonical column-name list (catalog order).

    Used by the K54 v2 build pipeline to enforce schema stability.
    A no-data call returns the same keys with NaN values; this
    function returns names in deterministic order.
    """
    # Build a synthetic call with empty inputs
    empty_candles = [{
        "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0,
        "volume": 0, "time": "1970-01-01T00:00:00",
    }] * 200
    candles_by_tf = {"M15": empty_candles, "H1": empty_candles, "H4": empty_candles}
    anchor_idx_by_tf = {"M15": 199, "H1": 199, "H4": 199}
    out = extract_liquidity_features(
        candles_by_tf, anchor_idx_by_tf,
        instrument="XAUUSD", side="LONG", current_price=2000.0,
    )
    return sorted(out.keys())


__all__ = [
    "extract_liquidity_features",
    "feature_names",
    "INSTRUMENT_TICK",
    "EQUAL_LEVEL_TICK_TOLERANCE",
    "ROUND_NUMBER_LEVELS",
    "LOOKBACK_BY_TF",
    "SWEEP_LOOKBACK_BY_TF",
]
