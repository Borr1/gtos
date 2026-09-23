"""Component 2 — Market State Analyzer.

Transforms raw OHLCV into structured market context.
All computations are deterministic — no AI.
Computes: swings, structure sequence, BOS/CHoCH, OBs, FVGs,
premium/discount zones, liquidity pools, sweeps.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Optional

from src.components.structure_detector_shadow_logger import (
    is_dual_compute_mode,
    log_structure_divergence,
    pick_production_label,
    resolve_detector_mode,
)
from src.components.poi_state_contract import (
    POI_STATE_SOURCE_BOUNDARY,
    candle_close_utc,
    finalize_poi_state,
    iso_utc,
    parse_utc,
    stable_poi_id,
)
from src.models.market_state_models import (
    BreakerBlock,
    DataQuality,
    EqualLevel,
    FairValueGap,
    LiquidityPool,
    LiquiditySweep,
    MarketStateObject,
    OrderBlock,
    PremiumDiscount,
    PriceZone,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    Swing,
    TimeframeState,
)
from src.utils.file_io import write_pipeline


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _resolve_detector_dead_zone_divisor(config: dict | None) -> int:
    """Return v2 structure dead-zone divisor from config, defaulting to 8."""
    if not isinstance(config, dict):
        return 8
    ms_cfg = config.get("market_state")
    if not isinstance(ms_cfg, dict):
        return 8
    try:
        return int(ms_cfg.get("v2_dead_zone_divisor", 8))
    except (TypeError, ValueError):
        return 8

def _get_most_recent_swing(swings: list[Swing], before_index: int,
                           swing_type: str) -> Optional[Swing]:
    """Return the most recent swing of *swing_type* whose candle index < *before_index*."""
    candidates = [s for s in swings if s.type == swing_type and s.index < before_index]
    return candidates[-1] if candidates else None


def _classify_each_swing(swings: list[Swing]) -> list[str]:
    """Label every swing as HH / HL / LH / LL relative to its predecessor of the same type."""
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]

    from src.judgment.state_choices import LEGACY, swing_label_choice

    high_labels: dict[int, str] = {}
    last_high = len(highs) - 1
    for i, h in enumerate(highs):
        if i == 0:
            high_labels[h.index] = "H"          # first — no comparison
            continue
        if i == last_high:
            chosen = swing_label_choice("high", h.price, highs[i - 1].price)
            if chosen is not LEGACY:
                if chosen in {"HH", "LH", "EH"}:
                    high_labels[h.index] = chosen
                continue
        if h.price > highs[i - 1].price:
            high_labels[h.index] = "HH"
        elif h.price < highs[i - 1].price:
            high_labels[h.index] = "LH"
        else:
            high_labels[h.index] = "EH"          # equal high

    low_labels: dict[int, str] = {}
    last_low = len(lows) - 1
    for i, lo in enumerate(lows):
        if i == 0:
            low_labels[lo.index] = "L"
            continue
        if i == last_low:
            chosen = swing_label_choice("low", lo.price, lows[i - 1].price)
            if chosen is not LEGACY:
                if chosen in {"HL", "LL", "EL"}:
                    low_labels[lo.index] = chosen
                continue
        if lo.price > lows[i - 1].price:
            low_labels[lo.index] = "HL"
        elif lo.price < lows[i - 1].price:
            low_labels[lo.index] = "LL"
        else:
            low_labels[lo.index] = "EL"

    merged = {**high_labels, **low_labels}
    return [merged[s.index] for s in swings if s.index in merged]


# ---------------------------------------------------------------------------
# Order-flow proxy computations (CLV, BVC) — I1 feature engineering
# ---------------------------------------------------------------------------

# Candle duration in minutes per timeframe — used for BVC sigma scaling
_TF_MINUTES: dict[str, int] = {"M15": 15, "H1": 60, "H4": 240, "D1": 1440}


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via Abramowitz & Stegun approximation (no scipy needed)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def compute_clv(candle: dict) -> float:
    """Close Location Value: (2*C - H - L) / (H - L).

    Range [-1, +1].  +1 = close at the high (buying pressure).
    -1 = close at the low (selling pressure).  0 = doji / midpoint close.
    Reference: Ha & Hu 2017 (L1 finding Q-1.7).
    """
    h = candle["high"]
    l = candle["low"]
    c = candle["close"]
    if h == l:
        return 0.0
    return (2.0 * c - h - l) / (h - l)


def compute_bvc(candle: dict, atr_14: float, tf_minutes: int = 15) -> float:
    """Bulk Volume Classification buy fraction [0, 1].

    Classifies the bar's volume as buying or selling based on where the close
    falls relative to the open, normalised by ATR-scaled volatility.
    Returns 0.5 when volume or ATR is unavailable (no information).
    Reference: Easley et al. 2016 (~76% accuracy on M15, L1 finding Q-1.7).
    """
    o = candle["open"]
    c = candle["close"]
    v = candle.get("volume", 0)

    if atr_14 <= 0 or v <= 0:
        return 0.5

    # Scale ATR from the base period (hourly) to the bar's timeframe
    sigma = atr_14 * math.sqrt(tf_minutes / 60.0)
    if sigma <= 0:
        return 0.5

    z = (c - o) / sigma
    return _norm_cdf(z)


def _in_session(time_str: str, start_hour: int, end_hour: int) -> bool:
    """Return True if *time_str* falls within [start_hour, end_hour) UTC.

    Works for ISO strings like "2026-03-28T07:15:00Z" or "2026-03-28 07:15:00".
    Returns False for short/synthetic test timestamps ("t0", "t1", etc.).
    """
    try:
        hour = int(time_str[11:13])
    except (ValueError, IndexError):
        return False
    if start_hour <= end_hour:
        return start_hour <= hour < end_hour
    # Session wraps midnight (e.g. Asian 22-03)
    return hour >= start_hour or hour < end_hour


def compute_session_atr(
    candles: list[dict],
    start_hour: int,
    end_hour: int,
    period: int = 14,
) -> Optional[float]:
    """ATR(14) computed using only candles from the specified UTC session window.

    Returns None when fewer than *period*+1 session candles are available.
    Reference: Ibikunle 2018 (W-shaped intraday vol for gold, L1 finding Q-1.6).
    """
    session_candles = [
        c for c in candles if _in_session(c["time"], start_hour, end_hour)
    ]
    if len(session_candles) < period + 1:
        return None

    trs: list[float] = []
    for i in range(1, len(session_candles)):
        h = session_candles[i]["high"]
        l = session_candles[i]["low"]
        prev_c = session_candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - prev_c), abs(l - prev_c)))

    if len(trs) < period:
        return None

    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


# ---------------------------------------------------------------------------
# Core algorithms
# ---------------------------------------------------------------------------

def detect_swings(candles: list[dict], min_bars: int = 2) -> list[Swing]:
    """Detect swing highs and lows.

    A swing high at index *i* requires ``candles[i].high`` to be strictly
    greater than the highs of *min_bars* candles on each side.  Mirror logic
    for swing lows.
    """
    swings: list[Swing] = []
    n = len(candles)
    last_eligible = n - min_bars - 1
    from src.judgment.state_choices import LEGACY, swing_bar_choice

    for i in range(min_bars, n - min_bars):
        if i == last_eligible:
            left_high = max(candles[i - j]["high"] for j in range(1, min_bars + 1))
            right_high = max(candles[i + j]["high"] for j in range(1, min_bars + 1))
            left_low = min(candles[i - j]["low"] for j in range(1, min_bars + 1))
            right_low = min(candles[i + j]["low"] for j in range(1, min_bars + 1))
            chosen = swing_bar_choice(
                index=i,
                center_high=candles[i]["high"],
                max_left_high=left_high,
                max_right_high=right_high,
                center_low=candles[i]["low"],
                min_left_low=left_low,
                min_right_low=right_low,
            )
            if chosen is not LEGACY:
                is_high, is_low = chosen
                if is_high is True:
                    swings.append(Swing(
                        index=i, type="high",
                        price=candles[i]["high"], time=candles[i]["time"],
                    ))
                if is_low is True:
                    swings.append(Swing(
                        index=i, type="low",
                        price=candles[i]["low"], time=candles[i]["time"],
                    ))
                continue
        is_swing_high = all(
            candles[i]["high"] > candles[i - j]["high"]
            and candles[i]["high"] > candles[i + j]["high"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_high:
            swings.append(Swing(
                index=i, type="high",
                price=candles[i]["high"], time=candles[i]["time"],
            ))

        is_swing_low = all(
            candles[i]["low"] < candles[i - j]["low"]
            and candles[i]["low"] < candles[i + j]["low"]
            for j in range(1, min_bars + 1)
        )
        if is_swing_low:
            swings.append(Swing(
                index=i, type="low",
                price=candles[i]["low"], time=candles[i]["time"],
            ))

    return sorted(swings, key=lambda s: s.index)


def identify_structure(swings: list[Swing]) -> StructureAnalysis:
    """Classify market structure from a list of swings.

    Returns bullish (HH + HL), bearish (LH + LL), transitional, or
    insufficient_data.
    """
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]

    if len(highs) < 2 or len(lows) < 2:
        return StructureAnalysis(
            direction="insufficient_data",
            protected_swing=None,
            swing_sequence=_classify_each_swing(swings),
        )

    hh_count = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i - 1].price)
    ll_count = sum(1 for i in range(1, len(lows)) if lows[i].price < lows[i - 1].price)
    hl_count = sum(1 for i in range(1, len(lows)) if lows[i].price > lows[i - 1].price)
    lh_count = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i - 1].price)

    recent_pairs = min(3, len(highs) - 1, len(lows) - 1)

    from src.judgment.state_choices import LEGACY, structure_direction_choice

    chosen = structure_direction_choice(hh_count, hl_count, ll_count, lh_count, recent_pairs)
    if chosen is not LEGACY:
        if chosen == "bullish":
            direction = "bullish"
            protected_swing = lows[-1]
        elif chosen == "bearish":
            direction = "bearish"
            protected_swing = highs[-1]
        else:
            direction = None
            protected_swing = None
    elif hh_count >= recent_pairs and hl_count >= recent_pairs:
        direction = "bullish"
        protected_swing = lows[-1]
    elif ll_count >= recent_pairs and lh_count >= recent_pairs:
        direction = "bearish"
        protected_swing = highs[-1]
    else:
        direction = "transitional"
        protected_swing = None

    return StructureAnalysis(
        direction=direction,
        protected_swing=protected_swing,
        swing_sequence=_classify_each_swing(swings),
        hh_count=hh_count,
        hl_count=hl_count,
        lh_count=lh_count,
        ll_count=ll_count,
    )


# ---------------------------------------------------------------------------
# identify_structure_v2 — net-score classifier (ADR-004 Option D)
# ---------------------------------------------------------------------------
#
# CEO-approved direction for the structural bullish-bias bug in v1
# ``identify_structure`` (see
# ``.context/06_decisions/ADR-004-market-state-structural-bullish-bias.md``).
# v1 has two compounding defects on realistic production windows:
#
#   1. ``recent_pairs = min(3, ...)`` saturates at 3, so in any window with
#      >=4 highs AND >=4 lows BOTH branches' threshold (>=3 each) is
#      satisfied.
#   2. The bullish branch is checked FIRST, so on 99.8% of 168-bar H1
#      production windows (V1 replay: 8,086 / 8,086 windows labeled
#      bullish across 5 instruments, Jan-Apr 2026), bullish wins by
#      precedence regardless of whether bearish evidence is numerically
#      stronger.
#
# v2 replaces the two-branch precedence tie-break with a single symmetric
# net-score classifier:
#
#     score      = (hh + hl) - (lh + ll)
#     dead_zone  = max(2, min_swings // 4)   # ~25% of pair transitions
#     bullish    iff score >  dead_zone
#     bearish    iff score < -dead_zone
#     transitional otherwise
#
# Mirrors ``identify_structure``'s signature exactly: same input, same
# ``StructureAnalysis`` return. PURE ADDITION — v1 remains the production
# code path and every call site (``_build_timeframe_state``, order blocks,
# premium/discount, knowledge_base, candidate_features_logger, ...) still
# consumes v1. Wiring to shadow logging (F2.3, separate wave) will consume
# v2 side-by-side with v1 before any production cutover.
#
# Design notes
# ~~~~~~~~~~~~
# * HH and HL are weighted equally (``hh + hl`` additive). An alternative
#   design weights HH higher than HL (HHs represent new highs); noted in
#   ADR-004 Option C "new bugs possible". Left unweighted for v2.
# * The dead zone scales with sample size: on a 2-swing-per-side window
#   (``min_swings=1``), the floor of 2 dominates (max(2, 0) = 2); on a
#   20-pair window (``min_swings=20``), threshold is max(2, 5) = 5. This
#   prevents tiny absolute-score differences from flipping the label on
#   very short windows.
# * Ties and near-ties fall into ``transitional``, consistent with the
#   Phase-2 audit framing that the detector should surface regime
#   ambiguity rather than coerce a direction.
# * Empty / single-swing inputs collapse to ``insufficient_data`` (same
#   rule as v1, so downstream consumers see identical degenerate
#   behaviour).
# * NaN / non-finite prices: a comparison with NaN always returns False,
#   so NaN-priced swings contribute 0 to every count; score stays 0 and
#   the dead zone labels the window ``transitional`` rather than
#   crashing.
#
# Invariants
# ~~~~~~~~~~
# * Symmetric by construction: swapping highs<->lows flips the sign of
#   score but preserves the dead-zone classification.
# * No "both branches qualify" state can exist — single score, disjoint
#   threshold regions.
# * Returns the same ``StructureAnalysis`` schema as v1 for drop-in
#   shadow comparison in downstream loggers.

def identify_structure_v2(
    swings: list[Swing],
    dead_zone_divisor: int = 8,
) -> StructureAnalysis:
    """Classify market structure via a net-score (ADR-004 Option D).

    Pure addition alongside ``identify_structure``; v1 remains the
    production code path until the F2.3 shadow-flag wiring lands.

    * score = (hh + hl) - (lh + ll)
    * dead_zone_threshold = max(2, min_swings // dead_zone_divisor)
    * ``bullish`` iff score > dead_zone_threshold
    * ``bearish`` iff score < -dead_zone_threshold
    * ``transitional`` otherwise
    * ``insufficient_data`` if fewer than 2 highs or 2 lows (same rule
      as v1, so downstream consumers see identical degenerate behaviour).

    Parameters
    ----------
    swings:
        Ordered list of detected highs and lows.
    dead_zone_divisor:
        Controls how aggressively ``transitional`` is called for
        moderately tilted windows. Larger divisors -> narrower dead zone
        -> more decisive bullish/bearish labels. Default ``8`` was
        selected by the 2026-04-24 F2-SWEEP replay across 5 instruments
        x Jan-Apr 2026: the ADR-004 recommended value ``4`` collapsed
        OB supply to 49% on USDJPY and produced 48% transitional vs
        the 10-30% ADR target band. Divisor ``8`` clears transitional
        band + OB supply preservation (>= 80% per instrument). Values
        ``<= 0`` are clamped to ``1`` (dead-zone threshold always at
        least the floor of 2).

        F2-SWEEP uses this to probe the preservation-vs-specificity
        tradeoff offline; see the archived
        ``research/archive/root_legacy_artifacts_2026_05_31/root_files/WAVE2_F2_SWEEP_REPORT.md``
        for the full divisor scoreboard.

    NaN / non-finite price values are treated as "no evidence" by the
    underlying comparisons (``nan > x`` and ``nan < x`` both evaluate
    False), which naturally pushes degenerate inputs into
    ``transitional`` rather than raising.
    """
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]

    if len(highs) < 2 or len(lows) < 2:
        return StructureAnalysis(
            direction="insufficient_data",
            protected_swing=None,
            swing_sequence=_classify_each_swing(swings),
        )

    # NaN-safe comparisons: any comparison with NaN returns False, so
    # NaN prices contribute 0 to every count. Degenerate inputs yield
    # score = 0 -> transitional (via the dead-zone arm) instead of
    # raising.
    hh_count = sum(
        1 for i in range(1, len(highs)) if highs[i].price > highs[i - 1].price
    )
    ll_count = sum(
        1 for i in range(1, len(lows)) if lows[i].price < lows[i - 1].price
    )
    hl_count = sum(
        1 for i in range(1, len(lows)) if lows[i].price > lows[i - 1].price
    )
    lh_count = sum(
        1 for i in range(1, len(highs)) if highs[i].price < highs[i - 1].price
    )

    bull_points = hh_count + hl_count
    bear_points = lh_count + ll_count
    score = bull_points - bear_points

    # Dead-zone threshold scales with sample size but never below 2.
    # min_swings counts the number of *transitions* on the thinner side
    # (swings - 1), matching how hh/hl/lh/ll are computed.
    min_swings = min(len(highs) - 1, len(lows) - 1)
    divisor = dead_zone_divisor if dead_zone_divisor > 0 else 1
    dead_zone_threshold = max(2, min_swings // divisor)

    if score > dead_zone_threshold:
        direction = "bullish"
        protected_swing = lows[-1]
    elif score < -dead_zone_threshold:
        direction = "bearish"
        protected_swing = highs[-1]
    else:
        direction = "transitional"
        protected_swing = None

    return StructureAnalysis(
        direction=direction,
        protected_swing=protected_swing,
        swing_sequence=_classify_each_swing(swings),
        hh_count=hh_count,
        hl_count=hl_count,
        lh_count=lh_count,
        ll_count=ll_count,
    )


def avg_candle_body(candles: list[dict], period: int = 20) -> float:
    """Return the average absolute candle body size over the last *period* candles."""
    recent = candles[-period:] if len(candles) >= period else candles
    if not recent:
        return 0.0
    bodies = [abs(c["close"] - c["open"]) for c in recent]
    return sum(bodies) / len(bodies)


def calculate_atr(candles: list[dict], period: int = 14) -> float:
    """Standard Average True Range calculation."""
    if len(candles) < 2:
        return 0.0
    true_ranges = []
    for i in range(1, len(candles)):
        high_low = candles[i]["high"] - candles[i]["low"]
        high_prev_close = abs(candles[i]["high"] - candles[i - 1]["close"])
        low_prev_close = abs(candles[i]["low"] - candles[i - 1]["close"])
        true_ranges.append(max(high_low, high_prev_close, low_prev_close))
    if not true_ranges:
        return 0.0
    if len(true_ranges) < period:
        return sum(true_ranges) / len(true_ranges)
    atr = sum(true_ranges[:period]) / period
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
    return atr


def detect_structure_breaks(
    candles: list[dict],
    swings: list[Swing],
    structure: StructureAnalysis,
) -> list[StructureEvent]:
    """Detect BOS and CHoCH events.

    * **BOS** — candle body closes beyond the most recent swing *in* the
      trend direction.
    * **CHoCH** — candle body closes beyond the protected swing *against*
      the trend direction.

    Each event is annotated with ``displacement_present`` and
    ``displacement_ratio`` (candle body / avg body).
    """
    if structure.direction in ("insufficient_data", "transitional") and structure.protected_swing is None:
        # For transitional without a protected swing we can still detect
        # BOS if there's clear structure, but per the arch doc the primary
        # logic keys off direction.  Return empty for safety.
        if structure.direction == "insufficient_data":
            return []

    avg_body = avg_candle_body(candles)
    events: list[StructureEvent] = []
    disp_ratios: list[float] = []
    # Track which swing levels have already been broken to avoid duplicates
    broken_bos_levels: set[float] = set()
    choch_fired = False

    for i, c in enumerate(candles):
        body = abs(c["close"] - c["open"])
        disp_ratio = body / avg_body if avg_body > 0 else 0.0
        disp_present = disp_ratio >= 1.5

        # --- BOS ---
        if structure.direction == "bullish":
            recent_high = _get_most_recent_swing(swings, before_index=i, swing_type="high")
            if (recent_high
                    and c["close"] > recent_high.price
                    and recent_high.price not in broken_bos_levels):
                broken_bos_levels.add(recent_high.price)
                events.append(StructureEvent(
                    type="BOS", direction="bullish",
                    level_broken=recent_high.price,
                    close_price=c["close"],
                    candle_index=i, time=c["time"],
                    displacement_present=disp_present,
                    displacement_ratio=round(disp_ratio, 2),
                ))
                disp_ratios.append(disp_ratio)
        elif structure.direction == "bearish":
            recent_low = _get_most_recent_swing(swings, before_index=i, swing_type="low")
            if (recent_low
                    and c["close"] < recent_low.price
                    and recent_low.price not in broken_bos_levels):
                broken_bos_levels.add(recent_low.price)
                events.append(StructureEvent(
                    type="BOS", direction="bearish",
                    level_broken=recent_low.price,
                    close_price=c["close"],
                    candle_index=i, time=c["time"],
                    displacement_present=disp_present,
                    displacement_ratio=round(disp_ratio, 2),
                ))
                disp_ratios.append(disp_ratio)

        # --- CHoCH ---
        # Only check for CHoCH on candles *after* the protected swing formed
        if structure.protected_swing and not choch_fired and i > structure.protected_swing.index:
            ps = structure.protected_swing
            if structure.direction == "bullish" and c["close"] < ps.price:
                choch_fired = True
                events.append(StructureEvent(
                    type="CHoCH", direction="bearish",
                    level_broken=ps.price,
                    close_price=c["close"],
                    candle_index=i, time=c["time"],
                    displacement_present=disp_present,
                    displacement_ratio=round(disp_ratio, 2),
                ))
                disp_ratios.append(disp_ratio)
            elif structure.direction == "bearish" and c["close"] > ps.price:
                choch_fired = True
                events.append(StructureEvent(
                    type="CHoCH", direction="bullish",
                    level_broken=ps.price,
                    close_price=c["close"],
                    candle_index=i, time=c["time"],
                    displacement_present=disp_present,
                    displacement_ratio=round(disp_ratio, 2),
                ))
                disp_ratios.append(disp_ratio)

    from src.judgment.state_choices import LEGACY, displacement_flags

    flags = displacement_flags(disp_ratios)
    if flags is not LEGACY:
        events = [
            ev.model_copy(update={"displacement_present": flag})
            for ev, flag in zip(events, flags)
        ]
    return events


def identify_order_blocks(
    candles: list[dict],
    structure_events: list[StructureEvent],
) -> list[OrderBlock]:
    """Identify order blocks from BOS and CHoCH events.

    For each BOS or CHoCH: walk backward up to 10 candles to find the last
    opposing candle (bearish candle before bullish break, vice-versa).  Mark
    as mitigated if price has returned to the OB zone after formation.

    Deduplicates by formation candle index — if the same candle produces an
    OB from both a CHoCH and a subsequent BOS, only the first is kept.

    ZONE FRESHNESS: OB zones are single-use. After the first retest
    (whether continuation or failure), the zone should not generate
    another CANDIDATE signal. Touch-1 continuation = 72.7% (n=23,575),
    Touch-2+ = 31.5% (n=82,572). See ob_zone_age_v1.md.

    Touch counting is performed by _count_touches() and is populated by
    _build_timeframe_state() on every emitted OB. The gate that acts on
    touch_count lives in permissions.py (reason: touch_count_too_high).
    """
    obs: list[OrderBlock] = []
    seen_formation_indices: set[int] = set()

    for event in structure_events:
        if event.type not in ("BOS", "CHoCH"):
            continue
        break_idx = event.candle_index

        if event.direction == "bullish":
            for j in range(break_idx - 1, max(break_idx - 10, -1), -1):
                if j < 0:
                    break
                if candles[j]["close"] < candles[j]["open"]:  # bearish candle
                    if j in seen_formation_indices:
                        break  # deduplicate
                    seen_formation_indices.add(j)
                    mitigated = any(
                        candles[k]["low"] <= candles[j]["high"]
                        for k in range(break_idx + 1, len(candles))
                    )
                    obs.append(OrderBlock(
                        type="bullish",
                        high=candles[j]["high"],
                        low=candles[j]["low"],
                        open=candles[j]["open"],
                        close=candles[j]["close"],
                        formation_index=j,
                        formation_time=candles[j]["time"],
                        causing_bos_index=break_idx,
                        mitigated=mitigated,
                        causing_event_type=event.type,
                    ))
                    break
        elif event.direction == "bearish":
            for j in range(break_idx - 1, max(break_idx - 10, -1), -1):
                if j < 0:
                    break
                if candles[j]["close"] > candles[j]["open"]:  # bullish candle
                    if j in seen_formation_indices:
                        break  # deduplicate
                    seen_formation_indices.add(j)
                    mitigated = any(
                        candles[k]["high"] >= candles[j]["low"]
                        for k in range(break_idx + 1, len(candles))
                    )
                    obs.append(OrderBlock(
                        type="bearish",
                        high=candles[j]["high"],
                        low=candles[j]["low"],
                        open=candles[j]["open"],
                        close=candles[j]["close"],
                        formation_index=j,
                        formation_time=candles[j]["time"],
                        causing_bos_index=break_idx,
                        mitigated=mitigated,
                        causing_event_type=event.type,
                    ))
                    break

    return obs


# ---------------------------------------------------------------------------
# Multi-touch tracking
#
# Touch definition (per spec):
#   A candle "touches" an OB when candle.high >= OB.low AND candle.low <= OB.high
#   (range overlap of the candle wick range with the zone).
#
# Counting (production semantics — BAR-OVERLAP, not transitions):
#   - Starts at formation_index + 1 (formation candle itself is EXCLUDED).
#   - Stops at the end of the provided candle list (latest candle).
#   - Every overlapping candle is +1 (no transition-based aggregation).
#
# Purpose:
#   Touch-1 OB retest WR = 72.7% (n=23,575)
#   Touch-2+ OB retest WR = 31.5% (n=82,572)
#   permissions.py rejects trades whose target OB has touch_count >= 2 with
#   reason="touch_count_too_high". See research/diagnostics/zone_age_analysis/.
#
# Production vs research semantics (INTENTIONAL — not a bug):
#   research/diagnostics/zone_age_analysis/compute_zone_age_v1.py counts
#   TRANSITIONS (increment only on zone entry, not on consecutive bars inside
#   the zone). Production here uses BAR-OVERLAP (every bar with range overlap
#   counts). The two methods diverge by up to ~50× at unbounded history, but
#   reconcile to 99.991% gate-decision agreement at the live 168-bar H1
#   lookback window (see DEFAULT_LOOKBACKS["H1"]=168 in data_ingestion.py).
#   Phase 3 T3 empirical (106,147 retest events): FN=0, FP=8 (0.009%, WR 12.5%
#   on FPs — null-indistinguishable). The 72.7/31.5 cliff is fully preserved.
#   Reference: research/b_deep_audit_2026-04-19/phase3/
#              T3_production_semantics_touch_count.md
# ---------------------------------------------------------------------------

def _count_touches(ob: "OrderBlock", candles: list[dict]) -> int:
    """Return the number of candles AFTER *ob*'s formation whose range
    overlaps the OB zone.

    *candles* must be the full candle list for the OB's timeframe (the same
    list passed to identify_order_blocks). The OB's formation_index is used
    as the reference; the formation candle itself is excluded.

    Returns 0 if there are no candles after formation.
    """
    start = ob.formation_index + 1
    if start >= len(candles):
        return 0

    count = 0
    for c in candles[start:]:
        # Range overlap of candle wick range [low, high] with OB [low, high].
        if c["high"] >= ob.low and c["low"] <= ob.high:
            count += 1
    return count


def identify_breaker_blocks(
    candles: list[dict],
    order_blocks: list[OrderBlock],
) -> list[BreakerBlock]:
    """Identify breaker blocks from mitigated order blocks.

    A breaker block forms when an OB is mitigated (price body closes through
    the zone) and the zone flips direction. Only unretested breakers are
    returned — once price retests from the other side, the breaker is consumed.

    A mitigated bullish OB → bearish breaker (resistance).
    A mitigated bearish OB → bullish breaker (support).
    """
    breakers: list[BreakerBlock] = []

    for ob in order_blocks:
        if not ob.mitigated:
            continue

        # Find the candle that mitigated the OB (body closed through zone)
        mitigation_idx = None
        mitigation_time = ""
        causing_event = "price_action"

        start_idx = ob.causing_bos_index + 1
        for k in range(start_idx, len(candles)):
            c = candles[k]
            body_close = c["close"]
            body_open = c["open"]
            body_top = max(body_close, body_open)
            body_bottom = min(body_close, body_open)

            if ob.type == "bullish":
                # Bullish OB mitigated = candle body closes below the OB low
                if body_close < ob.low:
                    mitigation_idx = k
                    mitigation_time = c["time"]
                    break
            elif ob.type == "bearish":
                # Bearish OB mitigated = candle body closes above the OB high
                if body_close > ob.high:
                    mitigation_idx = k
                    mitigation_time = c["time"]
                    break

        if mitigation_idx is None:
            continue

        # Breaker direction is OPPOSITE of the original OB
        if ob.type == "bullish":
            breaker_dir = "bearish"
        else:
            breaker_dir = "bullish"

        # Check if the breaker has been retested (price returned to zone from other side)
        is_retested = False
        for k in range(mitigation_idx + 1, len(candles)):
            c = candles[k]
            if breaker_dir == "bullish":
                # Bullish breaker (was bearish OB) — retest from below
                if c["low"] <= ob.high and c["close"] >= ob.low:
                    is_retested = True
                    break
            elif breaker_dir == "bearish":
                # Bearish breaker (was bullish OB) — retest from above
                if c["high"] >= ob.low and c["close"] <= ob.high:
                    is_retested = True
                    break

        breakers.append(BreakerBlock(
            zone_high=ob.high,
            zone_low=ob.low,
            direction=breaker_dir,
            original_ob_direction=ob.type,
            formation_time=ob.formation_time,
            mitigation_time=mitigation_time,
            causing_event=ob.causing_event_type,
            is_retested=is_retested,
            timeframe="H1",
        ))

    return breakers


def _fvg_predecision_state(
    *,
    candles: list[dict],
    confirmation_index: int,
    direction: str,
    zone_low: float,
    zone_high: float,
    symbol: str,
    timeframe: str,
) -> dict[str, object]:
    timeframe_minutes = _TF_MINUTES.get(timeframe, 15)
    source_indices = [confirmation_index - 2, confirmation_index - 1, confirmation_index]
    source_times = [iso_utc(candles[index].get("time")) for index in source_indices]
    created_at = candle_close_utc(
        candles[confirmation_index].get("time"),
        timeframe_minutes,
    )
    state_asof = candle_close_utc(candles[-1].get("time"), timeframe_minutes)
    touch_times: list[str] = []
    touch_episode_count = 0
    overlapping_previous = False
    max_mitigation_fraction = 0.0
    filled = False
    invalidated = False
    invalidation_time = ""
    invalidation_reason = ""
    terminal_time = ""
    terminal_reason = ""
    zone_width = max(0.0, zone_high - zone_low)
    for candle in candles[confirmation_index + 1 :]:
        candle_low = float(candle.get("low", 0.0) or 0.0)
        candle_high = float(candle.get("high", 0.0) or 0.0)
        candle_close = float(candle.get("close", 0.0) or 0.0)
        candle_time = candle_close_utc(candle.get("time"), timeframe_minutes)
        overlaps = candle_low <= zone_high and candle_high >= zone_low
        if overlaps:
            touch_times.append(candle_time)
            if not overlapping_previous:
                touch_episode_count += 1
            if zone_width > 0.0:
                penetration = (
                    (zone_high - candle_low) / zone_width
                    if direction == "bullish"
                    else (candle_high - zone_low) / zone_width
                )
                max_mitigation_fraction = max(
                    max_mitigation_fraction,
                    max(0.0, min(1.0, penetration)),
                )
        overlapping_previous = overlaps
        if direction == "bullish":
            if candle_close < zone_low:
                invalidated = True
                invalidation_time = candle_time
                invalidation_reason = "bullish_fvg_close_below_far_boundary"
                terminal_time = candle_time
                terminal_reason = invalidation_reason
                break
            if candle_low <= zone_low:
                filled = True
                terminal_time = candle_time
                terminal_reason = "bullish_fvg_wick_filled_far_boundary"
                break
        else:
            if candle_close > zone_high:
                invalidated = True
                invalidation_time = candle_time
                invalidation_reason = "bearish_fvg_close_above_far_boundary"
                terminal_time = candle_time
                terminal_reason = invalidation_reason
                break
            if candle_high >= zone_high:
                filled = True
                terminal_time = candle_time
                terminal_reason = "bearish_fvg_wick_filled_far_boundary"
                break
    created_dt = parse_utc(created_at)
    state_asof_dt = parse_utc(state_asof)
    age_hours = (
        max(0.0, (state_asof_dt - created_dt).total_seconds() / 3600.0)
        if created_dt is not None and state_asof_dt is not None
        else 0.0
    )
    touch_count = len(touch_times)
    mitigation_status = (
        "filled"
        if filled
        else "partially_mitigated"
        if touch_count
        else "untouched"
    )
    poi_id = stable_poi_id(
        symbol=symbol,
        timeframe=timeframe,
        poi_type="fair_value_gap",
        direction=direction,
        source_candle_times=source_times,
        zone_low=zone_low,
        zone_high=zone_high,
    )
    return finalize_poi_state(
        {
            "poi_id": poi_id,
            "poi_type": "fair_value_gap",
            "poi_timeframe": timeframe,
            "poi_direction": direction,
            "poi_zone_low": zone_low,
            "poi_zone_high": zone_high,
            "poi_source_candle_times": source_times,
            "poi_created_at_utc": created_at,
            "poi_state_asof_utc": state_asof,
            "poi_age_hours": age_hours,
            "poi_touch_count": touch_count,
            "poi_overlap_bar_count": touch_count,
            "poi_touch_episode_count": touch_episode_count,
            "poi_touch_count_semantics": "closed_candle_overlap_bar_count",
            "poi_max_mitigation_fraction": max_mitigation_fraction,
            "poi_first_touch_time_utc": touch_times[0] if touch_times else "",
            "poi_last_touch_time_utc": touch_times[-1] if touch_times else "",
            "poi_mitigation_status": mitigation_status,
            "poi_filled": filled,
            "poi_invalidated": invalidated,
            "poi_invalidation_time_utc": invalidation_time,
            "poi_invalidation_reason": invalidation_reason,
            "poi_terminal_time_utc": terminal_time,
            "poi_terminal_reason": terminal_reason,
            "poi_terminal_frozen": bool(terminal_time),
            "poi_state_source_boundary": POI_STATE_SOURCE_BOUNDARY,
            "poi_state_uses_outcome_fields": False,
        }
    )


def identify_fvgs(
    candles: list[dict],
    min_gap_size: float,
    *,
    symbol: str = "",
    timeframe: str = "M15",
) -> list[FairValueGap]:
    """Detect Fair Value Gaps (three-candle imbalance patterns).

    * Bullish FVG: ``candle[i+1].low - candle[i-1].high >= min_gap_size``
    * Bearish FVG: ``candle[i-1].low - candle[i+1].high >= min_gap_size``
    """
    fvgs: list[FairValueGap] = []
    for i in range(1, len(candles) - 1):
        # Bullish FVG
        bull_gap = candles[i + 1]["low"] - candles[i - 1]["high"]
        if bull_gap >= min_gap_size:
            top = candles[i + 1]["low"]
            bottom = candles[i - 1]["high"]
            poi_state = _fvg_predecision_state(
                candles=candles,
                confirmation_index=i + 1,
                direction="bullish",
                zone_low=bottom,
                zone_high=top,
                symbol=symbol,
                timeframe=timeframe,
            )
            fvgs.append(FairValueGap(
                type="bullish", top=top, bottom=bottom,
                midpoint=(top + bottom) / 2,
                candle_indices=[i - 1, i, i + 1],
                formation_time=candles[i]["time"],
                filled=bool(poi_state["poi_filled"]),
                timeframe=timeframe,
                poi_id=str(poi_state["poi_id"]),
                source_candle_times=list(poi_state["poi_source_candle_times"]),
                created_at_utc=str(poi_state["poi_created_at_utc"]),
                state_asof_utc=str(poi_state["poi_state_asof_utc"]),
                age_hours=float(poi_state["poi_age_hours"]),
                touch_count=int(poi_state["poi_touch_count"]),
                overlap_bar_count=int(poi_state["poi_overlap_bar_count"]),
                touch_episode_count=int(poi_state["poi_touch_episode_count"]),
                max_mitigation_fraction=float(
                    poi_state["poi_max_mitigation_fraction"]
                ),
                first_touch_time_utc=str(poi_state["poi_first_touch_time_utc"]),
                last_touch_time_utc=str(poi_state["poi_last_touch_time_utc"]),
                mitigation_status=str(poi_state["poi_mitigation_status"]),
                invalidated=bool(poi_state["poi_invalidated"]),
                invalidation_time_utc=str(poi_state["poi_invalidation_time_utc"]),
                invalidation_reason=str(poi_state["poi_invalidation_reason"]),
                terminal_time_utc=str(poi_state["poi_terminal_time_utc"]),
                terminal_reason=str(poi_state["poi_terminal_reason"]),
                terminal_frozen=bool(poi_state["poi_terminal_frozen"]),
                poi_state_hash_sha256=str(poi_state["poi_state_hash_sha256"]),
                poi_state_contract_status=str(poi_state["poi_state_contract_status"]),
                poi_state=poi_state,
            ))

        # Bearish FVG
        bear_gap = candles[i - 1]["low"] - candles[i + 1]["high"]
        if bear_gap >= min_gap_size:
            top = candles[i - 1]["low"]
            bottom = candles[i + 1]["high"]
            poi_state = _fvg_predecision_state(
                candles=candles,
                confirmation_index=i + 1,
                direction="bearish",
                zone_low=bottom,
                zone_high=top,
                symbol=symbol,
                timeframe=timeframe,
            )
            fvgs.append(FairValueGap(
                type="bearish", top=top, bottom=bottom,
                midpoint=(top + bottom) / 2,
                candle_indices=[i - 1, i, i + 1],
                formation_time=candles[i]["time"],
                filled=bool(poi_state["poi_filled"]),
                timeframe=timeframe,
                poi_id=str(poi_state["poi_id"]),
                source_candle_times=list(poi_state["poi_source_candle_times"]),
                created_at_utc=str(poi_state["poi_created_at_utc"]),
                state_asof_utc=str(poi_state["poi_state_asof_utc"]),
                age_hours=float(poi_state["poi_age_hours"]),
                touch_count=int(poi_state["poi_touch_count"]),
                overlap_bar_count=int(poi_state["poi_overlap_bar_count"]),
                touch_episode_count=int(poi_state["poi_touch_episode_count"]),
                max_mitigation_fraction=float(
                    poi_state["poi_max_mitigation_fraction"]
                ),
                first_touch_time_utc=str(poi_state["poi_first_touch_time_utc"]),
                last_touch_time_utc=str(poi_state["poi_last_touch_time_utc"]),
                mitigation_status=str(poi_state["poi_mitigation_status"]),
                invalidated=bool(poi_state["poi_invalidated"]),
                invalidation_time_utc=str(poi_state["poi_invalidation_time_utc"]),
                invalidation_reason=str(poi_state["poi_invalidation_reason"]),
                terminal_time_utc=str(poi_state["poi_terminal_time_utc"]),
                terminal_reason=str(poi_state["poi_terminal_reason"]),
                terminal_frozen=bool(poi_state["poi_terminal_frozen"]),
                poi_state_hash_sha256=str(poi_state["poi_state_hash_sha256"]),
                poi_state_contract_status=str(poi_state["poi_state_contract_status"]),
                poi_state=poi_state,
            ))

    return fvgs


def calculate_premium_discount(
    swings: list[Swing],
    structure: StructureAnalysis,
) -> Optional[PremiumDiscount]:
    """Calculate Fibonacci retracement zones from the most recent impulse leg.

    Returns ``None`` if insufficient data or impulse range is zero.
    """
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]

    if structure.direction == "bullish":
        if not lows or not highs:
            return None
        recent_low = lows[-1]
        recent_high = highs[-1]
        impulse_range = recent_high.price - recent_low.price
        if impulse_range <= 0:
            return None
        return PremiumDiscount(
            impulse_low=recent_low.price,
            impulse_high=recent_high.price,
            equilibrium_50=recent_high.price - impulse_range * 0.50,
            fib_62=recent_high.price - impulse_range * 0.618,
            fib_79=recent_high.price - impulse_range * 0.786,
            discount_zone=PriceZone(
                top=recent_high.price - impulse_range * 0.50,
                bottom=recent_low.price,
            ),
            premium_zone=PriceZone(
                top=recent_high.price,
                bottom=recent_high.price - impulse_range * 0.50,
            ),
            ote_zone=PriceZone(
                top=recent_high.price - impulse_range * 0.618,
                bottom=recent_high.price - impulse_range * 0.786,
            ),
        )

    elif structure.direction == "bearish":
        if not lows or not highs:
            return None
        recent_high = highs[-1]
        recent_low = lows[-1]
        impulse_range = recent_high.price - recent_low.price
        if impulse_range <= 0:
            return None
        return PremiumDiscount(
            impulse_low=recent_low.price,
            impulse_high=recent_high.price,
            equilibrium_50=recent_low.price + impulse_range * 0.50,
            fib_62=recent_low.price + impulse_range * 0.618,
            fib_79=recent_low.price + impulse_range * 0.786,
            discount_zone=PriceZone(
                top=recent_low.price + impulse_range * 0.50,
                bottom=recent_low.price,
            ),
            premium_zone=PriceZone(
                top=recent_high.price,
                bottom=recent_low.price + impulse_range * 0.50,
            ),
            ote_zone=PriceZone(
                top=recent_low.price + impulse_range * 0.786,
                bottom=recent_low.price + impulse_range * 0.618,
            ),
        )

    return None


def detect_sweeps(
    candles: list[dict],
    liquidity_pools: list[LiquidityPool],
) -> list[LiquiditySweep]:
    """Detect liquidity sweeps in the last 10 candles.

    * **Sweep**: wick beyond the pool level, but body closes inside.
    * **Run**: body closes beyond the pool level.
    """
    sweeps: list[LiquiditySweep] = []
    start = max(0, len(candles) - 10)

    for pool in liquidity_pools:
        for i in range(start, len(candles)):
            c = candles[i]
            body_top = max(c["open"], c["close"])
            body_bottom = min(c["open"], c["close"])

            if pool.side == "high":
                if c["high"] > pool.price and body_top < pool.price:
                    sweeps.append(LiquiditySweep(
                        pool=pool, sweep_type="sweep",
                        wick_extreme=c["high"], body_close=c["close"],
                        candle_index=i, time=c["time"],
                    ))
                elif c["close"] > pool.price:
                    sweeps.append(LiquiditySweep(
                        pool=pool, sweep_type="run",
                        wick_extreme=c["high"], body_close=c["close"],
                        candle_index=i, time=c["time"],
                    ))
            elif pool.side == "low":
                if c["low"] < pool.price and body_bottom > pool.price:
                    sweeps.append(LiquiditySweep(
                        pool=pool, sweep_type="sweep",
                        wick_extreme=c["low"], body_close=c["close"],
                        candle_index=i, time=c["time"],
                    ))
                elif c["close"] < pool.price:
                    sweeps.append(LiquiditySweep(
                        pool=pool, sweep_type="run",
                        wick_extreme=c["low"], body_close=c["close"],
                        candle_index=i, time=c["time"],
                    ))

    return sweeps


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _build_timeframe_state(
    candles: list[dict],
    min_bars: int,
    fvg_min_gap: float,
    tf_name: str = "",
    *,
    detector_mode: str = "v1",
    detector_dead_zone_divisor: int = 8,
    shadow_symbol: str = "",
    shadow_candle_time: str = "",
    shadow_log_path: Optional[str] = None,
    shadow_logging_enabled: bool = True,
) -> TimeframeState:
    """Run all analysis for a single timeframe.

    Positional-argument signature is preserved for backward compatibility
    with callers in ``tests/test_market_state.py`` and
    ``tests/test_breaker_blocks.py``. The four ``shadow_*`` /
    ``detector_mode`` kwargs below are the F2.3 shadow-mode extension
    points:

    * ``detector_mode`` — one of ``"v1"``, ``"v2_shadow"``, ``"v2"``.
      ``"v1"`` (default) preserves prior single-compute behaviour
      exactly; no v2 call, no logger call.
    * ``shadow_symbol``, ``shadow_candle_time``, ``shadow_log_path`` —
      forwarded to the divergence logger when dual-compute mode fires.
      Defaults keep the logger quiet for unit tests that don't care
      about the shadow path. ``shadow_log_path=None`` routes to the
      production default (``shadow_logs/structure_detector_divergences.jsonl``);
      tests pass a tmp_path to isolate writes.

    Dual-compute
    ~~~~~~~~~~~~
    In ``v2_shadow``, v1 drives production and v2 is log-only on
    disagreement. In ``v2`` (CEO cutover), v2 drives production and v1
    is log-only on disagreement — this gives a rollback-sanity window
    so late-surfacing problems still land in the same JSONL as the
    shadow phase. Either way, v1 and v2 are both computed exactly
    once per call; no redundant detection work.
    """
    swings = detect_swings(candles, min_bars=min_bars)

    # ------ F2.3 dual-compute ------
    # Default (v1 mode) takes the single-compute fast path to preserve
    # bit-exact prior behaviour. The dual-compute branch is only entered
    # when an opt-in mode is requested AND the structure is at least
    # well-formed enough that v2 won't be forced to insufficient_data.
    v1_label = identify_structure(swings)
    v2_label: Optional[StructureAnalysis] = None
    if is_dual_compute_mode(detector_mode):
        # identify_structure_v2 has the same signature and degenerate
        # behaviour as v1 (insufficient_data on <2 highs or <2 lows).
        v2_label = identify_structure_v2(
            swings,
            dead_zone_divisor=detector_dead_zone_divisor,
        )
        if shadow_logging_enabled and v1_label.direction != v2_label.direction:
            # Any divergence on any timeframe is a row. Crash-safety
            # lives inside the logger (try/except wrapper) so the
            # production v1 path cannot be broken by a disk-full or
            # permission error on shadow_logs/.
            log_kwargs: dict = {
                "symbol": shadow_symbol,
                "timeframe": tf_name,
                "v1_label": v1_label,
                "v2_label": v2_label,
                "detector_version_config": detector_mode,
                "production_label": pick_production_label(
                    detector_mode, v1_label, v2_label
                ),
                "candle_time": shadow_candle_time,
            }
            if shadow_log_path is not None:
                log_kwargs["log_path"] = shadow_log_path
            log_structure_divergence(**log_kwargs)

    structure = pick_production_label(detector_mode, v1_label, v2_label)
    structure_events = detect_structure_breaks(candles, swings, structure)
    order_blocks = identify_order_blocks(candles, structure_events)
    # Populate touch_count on every OB (not just the retest target). Uses
    # same-timeframe candles — H1 OB touches counted against H1 candles, etc.
    for ob in order_blocks:
        ob.touch_count = _count_touches(ob, candles)
    breaker_blocks = identify_breaker_blocks(candles, order_blocks)
    fvgs = identify_fvgs(
        candles,
        min_gap_size=fvg_min_gap,
        symbol=shadow_symbol,
        timeframe=tf_name or "M15",
    )
    pd_zones = calculate_premium_discount(swings, structure)
    avg_body = avg_candle_body(candles)
    atr = calculate_atr(candles, period=14)

    # --- CLV: current candle and 5-bar mean ---
    clv_current: Optional[float] = None
    clv_avg_5: Optional[float] = None
    if candles:
        clv_current = compute_clv(candles[-1])
        last5 = candles[-5:] if len(candles) >= 5 else candles
        clv_avg_5 = sum(compute_clv(c) for c in last5) / len(last5)

    # --- BVC: current buy fraction and 5-bar net flow ---
    bvc_buy_fraction: Optional[float] = None
    net_flow_5: Optional[float] = None
    if candles and atr > 0:
        tf_minutes = _TF_MINUTES.get(tf_name, 15)
        bvc_buy_fraction = compute_bvc(candles[-1], atr, tf_minutes)
        last5 = candles[-5:] if len(candles) >= 5 else candles
        net_flow_5 = sum(
            c.get("volume", 0) * (2.0 * compute_bvc(c, atr, tf_minutes) - 1.0)
            for c in last5
        )

    return TimeframeState(
        swings=swings,
        structure=structure,
        structure_events=structure_events,
        order_blocks=order_blocks,
        breaker_blocks=breaker_blocks,
        fair_value_gaps=fvgs,
        premium_discount=pd_zones,
        avg_candle_body=avg_body,
        atr_14=atr,
        clv_current=clv_current,
        clv_avg_5=clv_avg_5,
        bvc_buy_fraction=bvc_buy_fraction,
        net_flow_5=net_flow_5,
        # atr_session / session_vol_ratio set in compute_market_state for XAUUSD M15
    )


def _build_liquidity_pools(session_levels: SessionLevels,
                           equal_highs: list[EqualLevel],
                           equal_lows: list[EqualLevel]) -> list[LiquidityPool]:
    """Assemble the list of liquidity pools from session levels and equal levels."""
    pools: list[LiquidityPool] = []
    # Guard: skip high-side pools at 0.0 — causes spurious sweep detection
    if session_levels.asian_high > 0.0:
        pools.append(LiquidityPool(type="asian_high", price=session_levels.asian_high, side="high"))
    pools.append(LiquidityPool(type="asian_low", price=session_levels.asian_low, side="low"))
    if session_levels.pdh > 0.0:
        pools.append(LiquidityPool(type="pdh", price=session_levels.pdh, side="high"))
    pools.append(LiquidityPool(type="pdl", price=session_levels.pdl, side="low"))
    if session_levels.session_high is not None:
        pools.append(LiquidityPool(type="session_high", price=session_levels.session_high, side="high"))
    if session_levels.session_low is not None:
        pools.append(LiquidityPool(type="session_low", price=session_levels.session_low, side="low"))
    if session_levels.london_high is not None:
        pools.append(LiquidityPool(type="london_high", price=session_levels.london_high, side="high"))
    if session_levels.london_low is not None:
        pools.append(LiquidityPool(type="london_low", price=session_levels.london_low, side="low"))
    for eh in equal_highs:
        pools.append(LiquidityPool(type="equal_highs", price=eh.price, side="high"))
    for el in equal_lows:
        pools.append(LiquidityPool(type="equal_lows", price=el.price, side="low"))
    return pools


def compute_market_state(
    raw_data: dict,
    config: dict,
    *,
    timeframe_state_provider: Callable[..., TimeframeState] | None = None,
) -> MarketStateObject:
    """Orchestrate all market-state computations and return the full MSO.

    *raw_data* is the parsed ``01_raw_data.json``.
    *config* is the parsed ``agent_config.yaml``.

    Also writes to ``pipeline_state/02_market_state.json``.
    """
    data_cfg = config.get("data", {})
    market_state_cfg = config.get("market_state", {})
    market_state_cfg = market_state_cfg if isinstance(market_state_cfg, dict) else {}
    side_effect_writes_enabled = bool(
        market_state_cfg.get("side_effect_writes_enabled", True)
    )
    structure_shadow_log_enabled = bool(
        market_state_cfg.get(
            "structure_shadow_log_enabled",
            side_effect_writes_enabled,
        )
    )
    structure_shadow_log_path = market_state_cfg.get("structure_shadow_log_path")
    swing_bars = data_cfg.get("swing_detection_min_bars", {})
    fvg_gaps = data_cfg.get("fvg_min_gap", {})

    # F2.3: resolve detector mode once per MSO build. "v1" (default) keeps
    # every downstream call in the exact pre-F2.3 code path (single
    # identify_structure call, no v2 computation, no logger invocation).
    detector_mode = resolve_detector_mode(config)
    detector_dead_zone_divisor = _resolve_detector_dead_zone_divisor(config)
    shadow_symbol = raw_data.get("symbol", "")
    shadow_candle_time = raw_data.get("timestamp_utc", "")

    timeframes: dict[str, TimeframeState] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        candles = raw_data.get("candles", {}).get(tf, [])
        if not candles:
            timeframes[tf] = TimeframeState(
                structure=StructureAnalysis(direction="insufficient_data"),
            )
            continue
        mb = swing_bars.get(tf, 2)
        fg = fvg_gaps.get(tf, 1.0)
        build_parameters: dict[str, Any] = {
            "min_bars": mb,
            "fvg_min_gap": fg,
            "tf_name": tf,
            "detector_mode": detector_mode,
            "detector_dead_zone_divisor": detector_dead_zone_divisor,
            "shadow_symbol": shadow_symbol,
            "shadow_candle_time": shadow_candle_time,
            "shadow_log_path": (
                str(structure_shadow_log_path)
                if structure_shadow_log_path
                else None
            ),
            "shadow_logging_enabled": structure_shadow_log_enabled,
        }

        def build_timeframe_state() -> TimeframeState:
            return _build_timeframe_state(candles, **build_parameters)

        if tf in {"D1", "H4", "H1"} and timeframe_state_provider is not None:
            timeframes[tf] = timeframe_state_provider(
                timeframe=tf,
                candles=candles,
                build_parameters=build_parameters,
                builder=build_timeframe_state,
            )
        else:
            timeframes[tf] = build_timeframe_state()

    sl_data = raw_data.get("session_levels", {})
    session_levels = SessionLevels(
        asian_high=sl_data.get("asian_high", 0.0),
        asian_low=sl_data.get("asian_low", 0.0),
        pdh=sl_data.get("pdh", 0.0),
        pdl=sl_data.get("pdl", 0.0),
        session_high=sl_data.get("session_high"),
        session_low=sl_data.get("session_low"),
        london_high=sl_data.get("london_high"),
        london_low=sl_data.get("london_low"),
    )

    equal_highs = [
        EqualLevel(**eh) for eh in raw_data.get("equal_highs_H4", [])
    ] + [
        EqualLevel(**eh) for eh in raw_data.get("equal_highs_H1", [])
    ]
    equal_lows = [
        EqualLevel(**el) for el in raw_data.get("equal_lows_H4", [])
    ] + [
        EqualLevel(**el) for el in raw_data.get("equal_lows_H1", [])
    ]

    liquidity_pools = _build_liquidity_pools(session_levels, equal_highs, equal_lows)

    m15_candles = raw_data.get("candles", {}).get("M15", [])
    detected_sweeps = detect_sweeps(m15_candles, liquidity_pools) if m15_candles else []

    dq_raw = raw_data.get("data_quality", {})
    data_quality = DataQuality(
        all_timeframes_complete=dq_raw.get("all_timeframes_complete", False),
        spread_normal=dq_raw.get("spread_normal", False),
        mt5_connected=dq_raw.get("mt5_connected", False),
        timestamp_utc=dq_raw.get("timestamp_utc", raw_data.get("timestamp_utc", "")),
    )

    hi_events = raw_data.get("high_impact_events")

    # --- Session-specific ATR for XAUUSD M15 (Ibikunle 2018) ---
    # Gold has a W-shaped intraday vol pattern: London and NY sessions differ
    # from the overnight average.  Separate ATRs improve SL calibration.
    symbol = raw_data.get("symbol", "")
    if symbol == "XAUUSD" and "M15" in timeframes:
        m15_candles_full = raw_data.get("candles", {}).get("M15", [])
        atr_overall = timeframes["M15"].atr_14
        if m15_candles_full and atr_overall > 0:
            # Gold sessions (UTC): London 07-11, NY 13-17
            atr_london = compute_session_atr(m15_candles_full, 7, 11)
            atr_ny = compute_session_atr(m15_candles_full, 13, 17)

            current_ts = raw_data.get("timestamp_utc", "")
            try:
                current_hour = int(str(current_ts)[11:13])
            except (TypeError, ValueError):
                current_hour = None
            from src.judgment.state_choices import LEGACY, session_atr_choice

            chosen_window = session_atr_choice(current_hour) if current_hour is not None else LEGACY
            if current_hour is None:
                current_session_atr = None
            elif chosen_window is not LEGACY:
                if chosen_window == "london":
                    current_session_atr = atr_london
                elif chosen_window == "ny":
                    current_session_atr = atr_ny
                else:
                    current_session_atr = None
            elif _in_session(current_ts, 7, 11):
                current_session_atr = atr_london
            elif _in_session(current_ts, 13, 17):
                current_session_atr = atr_ny
            else:
                current_session_atr = None

            session_vol_ratio: Optional[float] = None
            if current_session_atr is not None:
                session_vol_ratio = round(current_session_atr / atr_overall, 2)

            timeframes["M15"] = timeframes["M15"].model_copy(update={
                "atr_session": current_session_atr,
                "session_vol_ratio": session_vol_ratio,
            })

    mso = MarketStateObject(
        timestamp_utc=raw_data.get("timestamp_utc", ""),
        timeframes=timeframes,
        session_levels=session_levels,
        equal_highs=equal_highs,
        equal_lows=equal_lows,
        liquidity_pools=liquidity_pools,
        detected_sweeps=detected_sweeps,
        spread_cents=raw_data.get("spread_cents"),
        high_impact_events=hi_events,
        data_quality=data_quality,
    )

    if side_effect_writes_enabled:
        write_pipeline("02_market_state.json", mso.model_dump())
    return mso
