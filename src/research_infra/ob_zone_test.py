"""F4 — Fresh OB-zone Test A re-test on H2-2026 data.

Pure-Python re-implementation of the canonical Test A methodology
(``.context/03_analysis/test_a_rerun_real_bos_results.md``) that
extracts BOS events FRESH from raw H1 OHLCV (no cached inputs) and
mechanically simulates two competing entry strategies on the same
population:

1. **OB retest** — pullback to 80% into the last opposing candle zone
   before the structural break (the canonical OB-pullback entry).
2. **Generic pullback** — pullback to 50% Fibonacci retracement of the
   impulse swing that broke structure (the "generic" baseline).

For each strategy we compute a mechanical entry, SL (buffer beyond the
zone / impulse extreme), TP (1.5R floor), and resolve the outcome via
walk-forward on M15 OHLCV using the same SL-first + same-bar-skip
contract as :mod:`src.research_infra.dumb_baseline`.

Why this exists
===============
K52 (`research/edge_decomposition/K52_survival/report.md`,
2026-04-26) re-tested the +17pp OB-zone advantage but reused the
**cached** Test A inputs (122/173 OB wins vs 73/136 baseline wins on
n=219 BOS events from a 2024-04 → 2026-03 batch). The corrected p
remained 0.0116 — but the population was unchanged, so this is a
"survives standardised pooled-z test" verdict, NOT a "survives on
freshly extracted current-data population" verdict. The strategic
question — has the OB-zone advantage actually decayed on H2-2026
data? — needed a fresh re-extract.

F4 closes that gap. We re-derive BOS events from raw OHLCV on the
2026-01-01 → 2026-04-24 window we have data for, and re-run the same
Q2 comparison ("OB vs 80% retrace" — but here we use 50% Fibonacci
retracement to follow the original Test A's "generic deep pullback"
framing more faithfully and avoid an entry point that is
arithmetically inside the OB zone for some BOS shapes).

Hard rules
==========
* **No AI / Anthropic API calls.** Phase 1 = $0. Pure-Python OHLCV replay.
* **Read-only inputs.** ``data/historical_2026/`` is read-only.
  Outputs go to a caller-supplied directory.
* **No production-code dependencies.** This file does not import from
  ``src/components/`` (production trading code), although it
  re-implements the same swing-detection + BOS rule used there.
* **Reuses dumb_baseline outcome resolver.** ``resolve_mechanical_outcome``
  is the canonical M15 walk-forward; we delegate to it after building
  a synthetic ``MechanicalSetup`` for each strategy.
* **Never fabricate.** When entry / SL / TP cannot be priced (degenerate
  swing, OB beyond reach, etc.), record the row with ``skip_reason``
  and exclude from rate aggregations.

Methodology — BOS detection (mirrors src/components/market_state.py)
====================================================================
For each H1 OHLCV bar series (per instrument):

1. **Swings**: a swing high at index ``i`` requires ``high[i] >
   high[i-k]`` AND ``high[i] > high[i+k]`` for all ``k ∈ [1, min_bars]``.
   Mirror logic for swing lows. ``min_bars = 2`` (matches production).
2. **Structure direction** (rolling): build the swing sequence; classify
   the most recent N=4 swings as bullish (HH+HL dominant) or bearish
   (LH+LL dominant), else transitional.
3. **BOS event**: a candle whose close exceeds the most recent swing
   in the direction of structure (bullish: close > recent swing high;
   bearish: close < recent swing low). Each swing level is consumed
   once (no duplicate BOS on the same level).

Methodology — OB retest entry
==============================
For each BOS event in direction D:
  - Walk back up to 10 candles from the BOS index to find the LAST
    opposing-side candle (D=bullish → last bearish candle; D=bearish
    → last bullish candle). That candle is the OB.
  - Entry = OB.low + 0.80 × (OB.high - OB.low) for LONG (bullish BOS);
            OB.high - 0.80 × (OB.high - OB.low) for SHORT (bearish BOS).
  - SL = OB.low - buffer (LONG) / OB.high + buffer (SHORT).
  - Buffer = max(0.25 × ATR_14_at_BOS, 5 × tick_size). Matches
    A1 dumb_baseline default config.
  - TP = entry + min_rr × (entry - SL) [LONG], with min_rr = 1.5.

Methodology — Generic pullback entry (50% Fibonacci)
=====================================================
For each BOS event in direction D:
  - Identify the impulse: the swing extreme that was broken (anchor)
    + the BOS close price (impulse end).
  - For LONG: anchor = recent swing LOW before BOS; impulse = anchor →
    BOS close. Entry = anchor + 0.50 × (BOS close - anchor).
  - For SHORT: anchor = recent swing HIGH before BOS; impulse = anchor →
    BOS close. Entry = anchor - 0.50 × (anchor - BOS close).
  - SL = anchor - buffer (LONG) / anchor + buffer (SHORT).
    (Conservative: SL beyond the impulse origin, matching the
    "generic deep pullback" interpretation in
    ``test_a_rerun_real_bos_results.md`` Q2.)
  - TP = entry + 1.5 × (entry - SL) (LONG) — same min_rr floor as OB.

Outcome resolution
==================
Both entries resolve via :func:`dumb_baseline.resolve_mechanical_outcome`
walking forward on M15 data:
  - Two-stage walk: wait for fill (limit-order semantics), then watch
    for TP / SL with SL-first conservative rule.
  - Same-bar fill+TP/SL → ``SAME_BAR``, ``realized_r=None``, excluded
    from WR.
  - Timeout (96 M15 bars = 24h hold) → mark-to-market on last close.

This guarantees both strategies are scored on identical OHLCV walk
semantics — the only difference is entry/SL/TP price.

Statistical test
================
Per-period two-proportion z-test (pooled variance) on
(OB_wins / OB_resolved) vs (Generic_wins / Generic_resolved). Reports
both raw p and Bonferroni-corrected p (family size 5, matching K52)
so the F4 verdict can be slotted directly into the K52 narrative.

Verdict format
==============
Three rows: Full window, H1-2026 only (Jan-Feb), H2-2026 only
(Mar-Apr). Status:
  - ``SURVIVES_FRESH`` — corrected p < 0.05 AND delta_pp ≥ +5pp on
    H2-2026 (the decay-watch period).
  - ``DECAYED_FRESH`` — corrected p ≥ 0.05 OR delta_pp < +5pp on H2.
  - ``INCONCLUSIVE_FRESH_SAMPLE`` — n_total < 30 on H2 (n_min floor).

Out of scope
============
* No multi-framework comparison (FVG / breaker / etc.). F4 specifically
  re-tests the OB-zone advantage finding.
* No backwards extension to pre-2026 data — the H2-2026 question is
  the strategic question; older data is in K52's cached numbers
  already.
* No realized-AI-R join — we are NOT comparing AI selection to
  mechanical here. F4 is "OB zone vs generic pullback", same as the
  original Test A Q2. The K50/A1/B12 series handles AI-vs-mechanical.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

# Reuse outcome resolver + setup dataclass from A1
from src.research_infra.dumb_baseline import (
    DEFAULT_OHLCV_DIR,
    MechanicalOutcome,
    MechanicalSetup,
    OHLCV_STEM,
    TICK_SIZE,
    _bisect_first_after,
    _canonical_symbol,
    _normalize_to_utc_minute,
    resolve_mechanical_outcome,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project-root resolution + default paths
# ---------------------------------------------------------------------------

# src/research_infra/ob_zone_test.py → project root is parents[2]
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

#: Harness version embedded in summary.json; bump when contract changes.
HARNESS_VERSION: str = "F4-v1"

#: Family size for Bonferroni correction (matches K52 canonical 5).
DEFAULT_FAMILY_SIZE: int = 5

#: Canonical retrace fraction for OB pullback entry (matches Test A).
RETRACE_PCT: float = 0.80

#: Canonical Fibonacci level for generic pullback entry (matches Test A).
FIB_PCT: float = 0.50

#: Default RR floor (mirrors ``risk.min_rr`` in agent_config.yaml).
DEFAULT_MIN_RR: float = 1.5

#: SL buffer config defaults (mirror ``risk.sl_buffer_*`` in agent_config.yaml).
DEFAULT_SL_BUFFER_ATR_MULT: float = 0.25
DEFAULT_SL_BUFFER_MIN_TICKS: int = 5

#: ATR period for the SL buffer.
ATR_PERIOD: int = 14

#: Maximum lookforward window for outcome resolution. 96 M15 bars = 24h.
DEFAULT_MAX_HOLD_BARS: int = 96

#: Swing fractal window (matches src/components/market_state.detect_swings).
SWING_MIN_BARS: int = 2

#: Walk-back window for OB candle (matches identify_order_blocks).
OB_LOOKBACK_BARS: int = 10

#: Recency window for structure direction (count last N swing pairs).
STRUCTURE_RECENT_N: int = 4

#: H1-2026 / H2-2026 split point (Jan-Feb = H1; Mar-Apr = H2).
H1_2026_END: dt.datetime = dt.datetime(2026, 3, 1, tzinfo=dt.timezone.utc)


# ---------------------------------------------------------------------------
# Pure data shapes
# ---------------------------------------------------------------------------


@dataclass
class BOSEvent:
    """A single Break-of-Structure event extracted from H1 OHLCV.

    All fields are pure floats / strings / datetimes — no pandas, no
    OHLCV references. Used as the input to both the OB-retest and the
    generic-pullback finders.
    """

    # Identity
    symbol: str
    bos_time: dt.datetime  # candle close time of the breaking H1 bar
    bos_index: int  # row index in the H1 OHLCV array
    direction: str  # "LONG" | "SHORT"

    # Break level
    swing_level_broken: float  # the swing high (LONG) or low (SHORT) that broke
    swing_time: dt.datetime  # time of the broken swing

    # Impulse anchor (the opposing swing that started the impulse)
    anchor_swing_price: float  # swing low (LONG) or high (SHORT) before BOS
    anchor_swing_time: dt.datetime
    anchor_swing_index: int

    # The breaking candle
    bos_close: float
    bos_high: float
    bos_low: float

    # ATR at the BOS (used for SL buffer)
    atr_at_bos: float

    # OB derived from the BOS (last opposing candle)
    ob_high: Optional[float] = None
    ob_low: Optional[float] = None
    ob_index: Optional[int] = None
    ob_time: Optional[dt.datetime] = None
    ob_skip_reason: Optional[str] = None  # None when OB resolved


@dataclass
class Outcome:
    """Per-strategy outcome for one BOS event.

    Wraps :class:`MechanicalOutcome` plus the entry / SL / TP / RR used.
    """

    bos_id: str
    strategy: str  # "ob_retest" | "generic_50pct"
    skip_reason: Optional[str]  # None on success
    entry: Optional[float]
    sl: Optional[float]
    tp: Optional[float]
    rr: Optional[float]
    outcome: Optional[str]  # "TP" | "SL" | "TIMEOUT" | "NO_ENTRY" | "SAME_BAR" | ...
    realized_r: Optional[float]
    bars_in_trade: Optional[int]
    exit_time: Optional[str]


@dataclass
class TestAReport:
    """Top-level F4 result.

    Attributes
    ----------
    n_bos_total : int
        Number of BOS events extracted from the population.
    period_full / period_h1 / period_h2 : dict
        Per-period summary block (n_bos, ob_wr, generic_wr, delta_pp,
        raw_p, corrected_p, status).
    per_instrument : dict
        Per-instrument summaries for the full window.
    """

    # Tell pytest this is NOT a test class (the leading "Test" trips
    # pytest's collection heuristic).
    __test__ = False

    harness_version: str
    generated_at: str
    start_date: str
    end_date: str
    instruments: Tuple[str, ...]
    family_size: int

    n_bos_total: int

    period_full: dict
    period_h1: dict
    period_h2: dict
    per_instrument: dict

    n_min_floor: int = 30
    delta_floor_pp: float = 5.0
    alpha: float = 0.05


# ---------------------------------------------------------------------------
# Utility — load OHLCV (H1 + M15)
# ---------------------------------------------------------------------------


_H1_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _load_h1_ohlcv(symbol: str, ohlcv_dir: Path) -> List[Dict[str, Any]]:
    """Load the H1 OHLCV CSV for ``symbol``. Cached per process.

    Header is ``time,open,high,low,close,volume``; ``time`` parsed to
    tz-aware UTC datetime. Returns a list of dicts ordered by time
    ascending. Empty list if the file is missing.
    """
    canonical = _canonical_symbol(symbol)
    cache_key = f"{canonical}|{ohlcv_dir}"
    if cache_key in _H1_CACHE:
        return _H1_CACHE[cache_key]
    stem = OHLCV_STEM.get(canonical) or OHLCV_STEM.get(canonical.upper()) or canonical
    path = ohlcv_dir / f"{stem}_H1.csv"
    if not path.exists():
        logger.warning("H1 OHLCV missing for %s: %s", symbol, path)
        _H1_CACHE[cache_key] = []
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 5:
                    continue
                rec = dict(zip(header, parts))
                ts = _normalize_to_utc_minute(rec.get("time"))
                if ts is None:
                    continue
                try:
                    rows.append({
                        "time": ts,
                        "open": float(rec["open"]),
                        "high": float(rec["high"]),
                        "low": float(rec["low"]),
                        "close": float(rec["close"]),
                    })
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError as exc:
        logger.warning("Cannot read %s: %s", path, exc)
        _H1_CACHE[cache_key] = []
        return []
    rows.sort(key=lambda r: r["time"])
    _H1_CACHE[cache_key] = rows
    return rows


# ---------------------------------------------------------------------------
# Pure swing / BOS detection (mirrors src/components/market_state.py)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Swing:
    index: int
    type: str  # "high" | "low"
    price: float
    time: dt.datetime


def _detect_swings(candles: Sequence[Mapping[str, Any]],
                   min_bars: int = SWING_MIN_BARS) -> List[_Swing]:
    """Detect swing highs / lows on a candle list.

    Mirrors :func:`src.components.market_state.detect_swings` exactly:
    a swing high at index ``i`` requires ``high[i]`` strictly greater
    than highs of ``min_bars`` candles on each side. Mirror for lows.
    """
    swings: List[_Swing] = []
    n = len(candles)
    for i in range(min_bars, n - min_bars):
        try:
            h_i = float(candles[i]["high"])
            l_i = float(candles[i]["low"])
        except (KeyError, TypeError, ValueError):
            continue
        is_high = True
        is_low = True
        for k in range(1, min_bars + 1):
            try:
                h_left = float(candles[i - k]["high"])
                h_right = float(candles[i + k]["high"])
                l_left = float(candles[i - k]["low"])
                l_right = float(candles[i + k]["low"])
            except (KeyError, TypeError, ValueError):
                is_high = False
                is_low = False
                break
            if not (h_i > h_left and h_i > h_right):
                is_high = False
            if not (l_i < l_left and l_i < l_right):
                is_low = False
            if not is_high and not is_low:
                break
        if is_high:
            swings.append(_Swing(
                index=i, type="high", price=h_i,
                time=candles[i]["time"],
            ))
        if is_low:
            swings.append(_Swing(
                index=i, type="low", price=l_i,
                time=candles[i]["time"],
            ))
    return sorted(swings, key=lambda s: s.index)


def _classify_structure(swings: Sequence[_Swing], up_to_index: int) -> str:
    """Classify the structure direction using the most recent N swings
    formed strictly before ``up_to_index``.

    Returns one of "bullish", "bearish", "transitional", "insufficient_data".

    Rule: among the most-recent ``STRUCTURE_RECENT_N`` swings (mixed
    high/low) before ``up_to_index``, count HH/HL/LH/LL transitions.
    HH+HL ≥ 2 and bullish>bearish → bullish; LL+LH ≥ 2 and bearish>bullish
    → bearish; else transitional.
    """
    prior = [s for s in swings if s.index < up_to_index]
    if len(prior) < 4:
        return "insufficient_data"
    # Take last STRUCTURE_RECENT_N swings (mixed type)
    window = prior[-(STRUCTURE_RECENT_N + 1):]  # +1 to count transitions
    highs = [s for s in window if s.type == "high"]
    lows = [s for s in window if s.type == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient_data"
    hh = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i - 1].price)
    lh = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i - 1].price)
    hl = sum(1 for i in range(1, len(lows)) if lows[i].price > lows[i - 1].price)
    ll = sum(1 for i in range(1, len(lows)) if lows[i].price < lows[i - 1].price)
    bull_score = hh + hl
    bear_score = lh + ll
    if bull_score >= 2 and bull_score > bear_score:
        return "bullish"
    if bear_score >= 2 and bear_score > bull_score:
        return "bearish"
    return "transitional"


def _most_recent_swing(
    swings: Sequence[_Swing], before_index: int, swing_type: str
) -> Optional[_Swing]:
    """Return the most recent swing of a given type before ``before_index``."""
    candidates = [s for s in swings if s.index < before_index and s.type == swing_type]
    if not candidates:
        return None
    return max(candidates, key=lambda s: s.index)


def _calc_atr(candles: Sequence[Mapping[str, Any]],
              up_to_index: int,
              period: int = ATR_PERIOD) -> float:
    """Wilder ATR over the ``period`` bars ending at ``up_to_index - 1``.

    Returns 0.0 if insufficient bars. Uses true range = max(high-low,
    |high - prev_close|, |low - prev_close|).
    """
    if up_to_index <= period:
        return 0.0
    trs: List[float] = []
    for i in range(up_to_index - period, up_to_index):
        if i <= 0:
            continue
        try:
            high = float(candles[i]["high"])
            low = float(candles[i]["low"])
            prev_close = float(candles[i - 1]["close"])
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if not trs:
        return 0.0
    return sum(trs) / len(trs)


def _find_ob_for_bos(
    candles: Sequence[Mapping[str, Any]], bos_index: int, bos_direction: str
) -> Tuple[Optional[float], Optional[float], Optional[int], Optional[str]]:
    """Walk back up to OB_LOOKBACK_BARS from ``bos_index`` to find the
    last opposing-side candle. Returns (high, low, index, skip_reason).

    For bullish BOS (LONG): last bearish candle before BOS index.
    For bearish BOS (SHORT): last bullish candle before BOS index.
    """
    start = max(0, bos_index - OB_LOOKBACK_BARS)
    for j in range(bos_index - 1, start - 1, -1):
        try:
            o = float(candles[j]["open"])
            c = float(candles[j]["close"])
            h = float(candles[j]["high"])
            low = float(candles[j]["low"])
        except (KeyError, TypeError, ValueError):
            continue
        if bos_direction == "LONG" and c < o:
            return h, low, j, None
        if bos_direction == "SHORT" and c > o:
            return h, low, j, None
    return None, None, None, "NO_OPPOSING_CANDLE_IN_LOOKBACK"


# ---------------------------------------------------------------------------
# Public API: BOS extraction
# ---------------------------------------------------------------------------


def extract_bos_events(
    ohlcv_path: Path,
    *,
    symbol: Optional[str] = None,
    start: Optional[dt.datetime] = None,
    end: Optional[dt.datetime] = None,
) -> List[BOSEvent]:
    """Extract Break-of-Structure events from an H1 OHLCV CSV.

    Implements the canonical Test A methodology — at every H1 candle
    that closes beyond the most-recent same-direction swing under a
    rolling structure classifier, emit a BOSEvent.

    Each swing-level is consumed at most once (no repeat BOS on the
    same level — matches production ``identify_order_blocks``
    semantics).

    Parameters
    ----------
    ohlcv_path :
        Path to the H1 CSV. Header must be
        ``time,open,high,low,close,volume`` (matches
        ``data/historical_2026/{SYMBOL}_H1.csv``).
    symbol :
        Symbol identifier embedded in returned BOSEvents. Defaults to
        the file stem with ``_H1`` stripped.
    start, end :
        Optional UTC datetime filters on the BOS time. ``None`` =
        no filter.

    Returns
    -------
    list[BOSEvent]
        In ascending BOS time order. Each event is annotated with the
        OB zone (last opposing candle) when one is resolvable; else
        ``ob_skip_reason`` is set.
    """
    if not ohlcv_path.exists():
        logger.warning("OHLCV path missing: %s", ohlcv_path)
        return []
    if symbol is None:
        stem = ohlcv_path.stem
        if stem.endswith("_H1"):
            symbol = stem[:-3]
        else:
            symbol = stem

    # Load
    rows: List[Dict[str, Any]] = []
    try:
        with ohlcv_path.open("r", encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 5:
                    continue
                rec = dict(zip(header, parts))
                ts = _normalize_to_utc_minute(rec.get("time"))
                if ts is None:
                    continue
                try:
                    rows.append({
                        "time": ts,
                        "open": float(rec["open"]),
                        "high": float(rec["high"]),
                        "low": float(rec["low"]),
                        "close": float(rec["close"]),
                    })
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError as exc:
        logger.warning("Cannot read %s: %s", ohlcv_path, exc)
        return []
    rows.sort(key=lambda r: r["time"])

    if len(rows) < SWING_MIN_BARS * 4:  # need enough for swing detection
        return []

    swings = _detect_swings(rows, min_bars=SWING_MIN_BARS)
    if len(swings) < 4:
        return []

    events: List[BOSEvent] = []
    consumed_levels: set = set()

    for i in range(STRUCTURE_RECENT_N + SWING_MIN_BARS, len(rows)):
        bar = rows[i]
        if start is not None and bar["time"] < start:
            continue
        if end is not None and bar["time"] > end:
            continue

        direction = _classify_structure(swings, up_to_index=i)
        if direction == "bullish":
            recent_high = _most_recent_swing(swings, before_index=i, swing_type="high")
            if recent_high is None:
                continue
            level = recent_high.price
            level_key = ("high", round(level, 6), recent_high.index)
            if level_key in consumed_levels:
                continue
            if bar["close"] > level:
                consumed_levels.add(level_key)
                anchor = _most_recent_swing(swings, before_index=i, swing_type="low")
                if anchor is None:
                    continue
                atr = _calc_atr(rows, up_to_index=i)
                ob_high, ob_low, ob_idx, ob_skip = _find_ob_for_bos(rows, i, "LONG")
                events.append(BOSEvent(
                    symbol=symbol,
                    bos_time=bar["time"],
                    bos_index=i,
                    direction="LONG",
                    swing_level_broken=level,
                    swing_time=recent_high.time,
                    anchor_swing_price=anchor.price,
                    anchor_swing_time=anchor.time,
                    anchor_swing_index=anchor.index,
                    bos_close=bar["close"],
                    bos_high=bar["high"],
                    bos_low=bar["low"],
                    atr_at_bos=atr,
                    ob_high=ob_high,
                    ob_low=ob_low,
                    ob_index=ob_idx,
                    ob_time=rows[ob_idx]["time"] if ob_idx is not None else None,
                    ob_skip_reason=ob_skip,
                ))
        elif direction == "bearish":
            recent_low = _most_recent_swing(swings, before_index=i, swing_type="low")
            if recent_low is None:
                continue
            level = recent_low.price
            level_key = ("low", round(level, 6), recent_low.index)
            if level_key in consumed_levels:
                continue
            if bar["close"] < level:
                consumed_levels.add(level_key)
                anchor = _most_recent_swing(swings, before_index=i, swing_type="high")
                if anchor is None:
                    continue
                atr = _calc_atr(rows, up_to_index=i)
                ob_high, ob_low, ob_idx, ob_skip = _find_ob_for_bos(rows, i, "SHORT")
                events.append(BOSEvent(
                    symbol=symbol,
                    bos_time=bar["time"],
                    bos_index=i,
                    direction="SHORT",
                    swing_level_broken=level,
                    swing_time=recent_low.time,
                    anchor_swing_price=anchor.price,
                    anchor_swing_time=anchor.time,
                    anchor_swing_index=anchor.index,
                    bos_close=bar["close"],
                    bos_high=bar["high"],
                    bos_low=bar["low"],
                    atr_at_bos=atr,
                    ob_high=ob_high,
                    ob_low=ob_low,
                    ob_index=ob_idx,
                    ob_time=rows[ob_idx]["time"] if ob_idx is not None else None,
                    ob_skip_reason=ob_skip,
                ))

    return events


# ---------------------------------------------------------------------------
# Public API: per-strategy outcome resolvers
# ---------------------------------------------------------------------------


def _make_setup(
    bos: BOSEvent,
    *,
    entry: float,
    sl: float,
    tp: float,
) -> MechanicalSetup:
    """Wrap (entry, SL, TP) into a MechanicalSetup so the canonical
    A1 outcome resolver can score it.
    """
    sl_dist = abs(entry - sl)
    rr = abs(tp - entry) / sl_dist if sl_dist > 0 else 0.0
    bos_id = f"{bos.symbol}|{bos.bos_time.isoformat()}"
    return MechanicalSetup(
        cand_id=bos_id,
        symbol=_canonical_symbol(bos.symbol),
        candle_close_time=bos.bos_time,
        side=bos.direction,
        framework="ob_retest",
        ob_high=bos.ob_high or 0.0,
        ob_low=bos.ob_low or 0.0,
        ob_formation_time=bos.ob_time.isoformat() if bos.ob_time else None,
        ob_mitigated=False,
        ob_source_tf="H1",
        entry=round(entry, 6),
        sl=round(sl, 6),
        tp=round(tp, 6),
        rr=round(rr, 4),
        sl_buffer_used=0.0,
        h1_atr=bos.atr_at_bos,
        tick_size=TICK_SIZE.get(_canonical_symbol(bos.symbol), 0.01),
        selection_reason="OK",
        tp_source="rr_floor",
        skip_reason=None,
    )


def _sl_buffer(bos: BOSEvent, *, atr_mult: float, min_ticks: int) -> float:
    """Compute the SL buffer matching A1 dumb_baseline default config."""
    tick = TICK_SIZE.get(_canonical_symbol(bos.symbol), 0.01)
    atr_buf = atr_mult * bos.atr_at_bos if bos.atr_at_bos > 0 else 0.0
    tick_buf = min_ticks * tick
    return max(atr_buf, tick_buf)


def find_ob_retest_outcome(
    bos: BOSEvent,
    ohlcv_path: Path,
    *,
    retrace_pct: float = RETRACE_PCT,
    atr_mult: float = DEFAULT_SL_BUFFER_ATR_MULT,
    min_ticks: int = DEFAULT_SL_BUFFER_MIN_TICKS,
    min_rr: float = DEFAULT_MIN_RR,
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
    m15_ohlcv_dir: Optional[Path] = None,
    ohlcv_rows: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Outcome:
    """Compute mechanical OB-retest outcome (80% retrace into OB).

    Returns an :class:`Outcome` with ``skip_reason`` set when the OB
    cannot be priced (no opposing candle in lookback / degenerate OB).
    """
    bos_id = f"{bos.symbol}|{bos.bos_time.isoformat()}"
    if bos.ob_skip_reason is not None:
        return Outcome(
            bos_id=bos_id,
            strategy="ob_retest",
            skip_reason=bos.ob_skip_reason,
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )
    if bos.ob_high is None or bos.ob_low is None:
        return Outcome(
            bos_id=bos_id, strategy="ob_retest", skip_reason="NO_OB_PRICES",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )
    if bos.ob_high <= bos.ob_low:
        return Outcome(
            bos_id=bos_id, strategy="ob_retest", skip_reason="DEGENERATE_OB",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )

    ob_range = bos.ob_high - bos.ob_low
    if bos.direction == "LONG":
        entry = bos.ob_low + retrace_pct * ob_range
    else:
        entry = bos.ob_high - retrace_pct * ob_range

    buffer = _sl_buffer(bos, atr_mult=atr_mult, min_ticks=min_ticks)
    if buffer <= 0:
        return Outcome(
            bos_id=bos_id, strategy="ob_retest", skip_reason="BAD_SL_BUFFER",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )

    if bos.direction == "LONG":
        sl = bos.ob_low - buffer
    else:
        sl = bos.ob_high + buffer

    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return Outcome(
            bos_id=bos_id, strategy="ob_retest", skip_reason="DEGENERATE_SL",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )

    if bos.direction == "LONG":
        tp = entry + min_rr * sl_dist
    else:
        tp = entry - min_rr * sl_dist

    setup = _make_setup(bos, entry=entry, sl=sl, tp=tp)
    if m15_ohlcv_dir is None:
        m15_ohlcv_dir = DEFAULT_OHLCV_DIR
    out = resolve_mechanical_outcome(
        setup, m15_ohlcv_dir, max_hold_bars=max_hold_bars,
        ohlcv_rows=ohlcv_rows,
    )
    return Outcome(
        bos_id=bos_id,
        strategy="ob_retest",
        skip_reason=out.skip_reason,
        entry=round(entry, 6),
        sl=round(sl, 6),
        tp=round(tp, 6),
        rr=round(abs(tp - entry) / sl_dist, 4) if sl_dist > 0 else None,
        outcome=out.outcome,
        realized_r=out.realized_r,
        bars_in_trade=out.bars_in_trade,
        exit_time=out.exit_time,
    )


def find_generic_pullback_outcome(
    bos: BOSEvent,
    ohlcv_path: Path,
    *,
    fib_pct: float = FIB_PCT,
    atr_mult: float = DEFAULT_SL_BUFFER_ATR_MULT,
    min_ticks: int = DEFAULT_SL_BUFFER_MIN_TICKS,
    min_rr: float = DEFAULT_MIN_RR,
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
    m15_ohlcv_dir: Optional[Path] = None,
    ohlcv_rows: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Outcome:
    """Compute mechanical generic-pullback outcome (50% Fibonacci retrace).

    The "generic deep pullback" baseline from Test A Q2: enter at the
    50% Fibonacci retracement of the impulse swing (anchor swing →
    BOS close).
    """
    bos_id = f"{bos.symbol}|{bos.bos_time.isoformat()}"
    impulse_range = bos.bos_close - bos.anchor_swing_price
    if abs(impulse_range) < 1e-9:
        return Outcome(
            bos_id=bos_id, strategy="generic_50pct", skip_reason="DEGENERATE_IMPULSE",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )
    if bos.direction == "LONG":
        if impulse_range <= 0:
            return Outcome(
                bos_id=bos_id, strategy="generic_50pct",
                skip_reason="INVERTED_IMPULSE",
                entry=None, sl=None, tp=None, rr=None,
                outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
            )
        entry = bos.anchor_swing_price + fib_pct * impulse_range
    else:  # SHORT
        if impulse_range >= 0:
            return Outcome(
                bos_id=bos_id, strategy="generic_50pct",
                skip_reason="INVERTED_IMPULSE",
                entry=None, sl=None, tp=None, rr=None,
                outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
            )
        entry = bos.anchor_swing_price + fib_pct * impulse_range

    buffer = _sl_buffer(bos, atr_mult=atr_mult, min_ticks=min_ticks)
    if buffer <= 0:
        return Outcome(
            bos_id=bos_id, strategy="generic_50pct", skip_reason="BAD_SL_BUFFER",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )

    # SL beyond the impulse anchor (the "generic deep pullback" SL —
    # if the impulse origin breaks, the impulse hypothesis is wrong).
    if bos.direction == "LONG":
        sl = bos.anchor_swing_price - buffer
    else:
        sl = bos.anchor_swing_price + buffer

    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return Outcome(
            bos_id=bos_id, strategy="generic_50pct", skip_reason="DEGENERATE_SL",
            entry=None, sl=None, tp=None, rr=None,
            outcome=None, realized_r=None, bars_in_trade=None, exit_time=None,
        )

    if bos.direction == "LONG":
        tp = entry + min_rr * sl_dist
    else:
        tp = entry - min_rr * sl_dist

    setup = _make_setup(bos, entry=entry, sl=sl, tp=tp)
    if m15_ohlcv_dir is None:
        m15_ohlcv_dir = DEFAULT_OHLCV_DIR
    out = resolve_mechanical_outcome(
        setup, m15_ohlcv_dir, max_hold_bars=max_hold_bars,
        ohlcv_rows=ohlcv_rows,
    )
    return Outcome(
        bos_id=bos_id,
        strategy="generic_50pct",
        skip_reason=out.skip_reason,
        entry=round(entry, 6),
        sl=round(sl, 6),
        tp=round(tp, 6),
        rr=round(abs(tp - entry) / sl_dist, 4) if sl_dist > 0 else None,
        outcome=out.outcome,
        realized_r=out.realized_r,
        bars_in_trade=out.bars_in_trade,
        exit_time=out.exit_time,
    )


# ---------------------------------------------------------------------------
# Pure stats — minimum dependency two-prop z-test + Fisher exact
# ---------------------------------------------------------------------------


def _two_prop_z_test(wins_a: int, n_a: int, wins_b: int, n_b: int) -> float:
    """Two-sided pooled-variance two-proportion z-test p-value.

    Identical formulation to K52's ``two_sample_wr_test`` to keep p-values
    directly comparable. Uses the standard normal CDF approximation.
    Returns NaN on degenerate inputs.
    """
    if n_a <= 0 or n_b <= 0:
        return float("nan")
    p_a = wins_a / n_a
    p_b = wins_b / n_b
    p_pool = (wins_a + wins_b) / (n_a + n_b)
    if p_pool <= 0 or p_pool >= 1:
        return 1.0  # No variance → no signal
    se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n_a + 1.0 / n_b))
    if se <= 0:
        return 1.0
    z = (p_a - p_b) / se
    # Two-sided p via complementary error function
    return math.erfc(abs(z) / math.sqrt(2.0))


def bonferroni_correct(p: float, family_size: int = DEFAULT_FAMILY_SIZE) -> float:
    """Cap raw_p × family_size at 1.0. Returns NaN unchanged."""
    if not math.isfinite(p):
        return float("nan")
    return min(1.0, p * family_size)


# ---------------------------------------------------------------------------
# Period aggregation + status classification
# ---------------------------------------------------------------------------


def _aggregate_period(
    bos_list: Sequence[BOSEvent],
    ob_outcomes: Sequence[Outcome],
    generic_outcomes: Sequence[Outcome],
    *,
    period_label: str,
    family_size: int,
    n_min: int,
    delta_floor_pp: float,
    alpha: float,
) -> dict:
    """Compute WR / delta / p-values + status for one period."""
    n_bos = len(bos_list)

    # Resolved = realized_r is not None (filled + TP/SL/TIMEOUT) AND
    # not SAME_BAR / NO_DATA. NO_ENTRY excluded (mechanical never filled,
    # so it didn't actually happen — same as Test A's "filled" tally).
    def _wins_n(outs: Sequence[Outcome]) -> Tuple[int, int, int]:
        filled = 0
        resolved = 0
        wins = 0
        for o in outs:
            if o.skip_reason is not None and o.outcome is None:
                continue
            if o.outcome == "NO_ENTRY":
                continue
            filled += 1
            if o.realized_r is None:
                continue
            resolved += 1
            if o.realized_r > 0:
                wins += 1
        return wins, resolved, filled

    ob_wins, ob_resolved, ob_filled = _wins_n(ob_outcomes)
    gen_wins, gen_resolved, gen_filled = _wins_n(generic_outcomes)

    ob_wr = (ob_wins / ob_resolved) if ob_resolved > 0 else float("nan")
    gen_wr = (gen_wins / gen_resolved) if gen_resolved > 0 else float("nan")
    if math.isfinite(ob_wr) and math.isfinite(gen_wr):
        delta_pp = (ob_wr - gen_wr) * 100.0
    else:
        delta_pp = float("nan")

    raw_p = _two_prop_z_test(ob_wins, ob_resolved, gen_wins, gen_resolved)
    corrected_p = bonferroni_correct(raw_p, family_size)

    n_total = ob_resolved + gen_resolved
    if n_bos == 0:
        status = "INCONCLUSIVE_FRESH_SAMPLE"
        notes = "No BOS events extracted in this period."
    elif min(ob_resolved, gen_resolved) < n_min:
        status = "INCONCLUSIVE_FRESH_SAMPLE"
        notes = (f"Min resolved n = {min(ob_resolved, gen_resolved)} below "
                 f"floor n_min = {n_min} (per-arm).")
    elif not math.isfinite(corrected_p):
        status = "INCONCLUSIVE_FRESH_SAMPLE"
        notes = "Non-finite p-value (degenerate counts)."
    elif corrected_p < alpha and math.isfinite(delta_pp) and delta_pp >= delta_floor_pp:
        status = "SURVIVES_FRESH"
        notes = (f"Corrected p = {corrected_p:.4g} < α = {alpha} AND "
                 f"delta = +{delta_pp:.1f}pp ≥ floor +{delta_floor_pp}pp.")
    else:
        status = "DECAYED_FRESH"
        if not math.isfinite(delta_pp):
            notes = "Cannot compute delta — degenerate WR."
        elif corrected_p >= alpha and delta_pp < delta_floor_pp:
            notes = (f"Corrected p = {corrected_p:.4g} ≥ α = {alpha} AND "
                     f"delta = {delta_pp:.1f}pp < floor +{delta_floor_pp}pp.")
        elif corrected_p >= alpha:
            notes = (f"Corrected p = {corrected_p:.4g} ≥ α = {alpha} "
                     f"(delta = {delta_pp:.1f}pp).")
        else:
            notes = (f"Delta = {delta_pp:.1f}pp < floor +{delta_floor_pp}pp "
                     f"(corrected p = {corrected_p:.4g}).")

    return {
        "period_label": period_label,
        "n_bos": n_bos,
        "ob_wins": ob_wins,
        "ob_resolved": ob_resolved,
        "ob_filled": ob_filled,
        "ob_wr": ob_wr,
        "gen_wins": gen_wins,
        "gen_resolved": gen_resolved,
        "gen_filled": gen_filled,
        "gen_wr": gen_wr,
        "delta_pp": delta_pp,
        "raw_p": raw_p,
        "corrected_p": corrected_p,
        "status": status,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Public API: end-to-end Test A driver
# ---------------------------------------------------------------------------


def run_test_a_fresh(
    start_date: dt.datetime,
    end_date: dt.datetime,
    instruments: Sequence[str],
    ohlcv_dir: Path = DEFAULT_OHLCV_DIR,
    *,
    family_size: int = DEFAULT_FAMILY_SIZE,
    n_min: int = 30,
    delta_floor_pp: float = 5.0,
    alpha: float = 0.05,
    h2_2026_split: dt.datetime = H1_2026_END,
    progress: Optional[Callable[[str], None]] = None,
) -> Tuple[TestAReport, List[BOSEvent], List[Outcome], List[Outcome]]:
    """End-to-end fresh Test A.

    For each instrument:
      1. Extract BOS events from H1 OHLCV.
      2. Compute OB-retest + generic-pullback outcomes for each.
      3. Aggregate per-period (Full / H1-2026 / H2-2026) + per-instrument.

    Returns the report, the BOS events, and the per-strategy outcome
    lists (parallel-indexed to bos_events). Outcomes for events with
    failed BOS extraction (no OB / degenerate impulse) carry
    ``skip_reason`` and contribute to the resolved count via
    ``_aggregate_period``'s "filled = 0 → exclude" rule.
    """
    if progress is None:
        def progress(msg: str) -> None:  # noqa: ARG001
            pass

    all_bos: List[BOSEvent] = []
    all_ob: List[Outcome] = []
    all_gen: List[Outcome] = []

    per_instrument: Dict[str, dict] = {}

    for sym in instruments:
        canonical = _canonical_symbol(sym)
        stem = OHLCV_STEM.get(canonical) or OHLCV_STEM.get(canonical.upper()) or canonical
        h1_path = ohlcv_dir / f"{stem}_H1.csv"
        progress(f"Extracting BOS for {sym} from {h1_path.name}")
        bos = extract_bos_events(h1_path, symbol=sym, start=start_date, end=end_date)
        progress(f"  → {len(bos)} BOS events")

        # Compute outcomes per BOS
        ob_outcomes: List[Outcome] = []
        gen_outcomes: List[Outcome] = []
        for b in bos:
            ob_o = find_ob_retest_outcome(b, h1_path, m15_ohlcv_dir=ohlcv_dir)
            gen_o = find_generic_pullback_outcome(b, h1_path, m15_ohlcv_dir=ohlcv_dir)
            ob_outcomes.append(ob_o)
            gen_outcomes.append(gen_o)

        # Per-instrument aggregate (full window only)
        per_instrument[sym] = _aggregate_period(
            bos, ob_outcomes, gen_outcomes,
            period_label=f"full_{sym}",
            family_size=family_size,
            n_min=n_min,
            delta_floor_pp=delta_floor_pp,
            alpha=alpha,
        )

        all_bos.extend(bos)
        all_ob.extend(ob_outcomes)
        all_gen.extend(gen_outcomes)

    # Period splits
    full_bos, full_ob, full_gen = all_bos, all_ob, all_gen

    h1_idx = [i for i, b in enumerate(full_bos) if b.bos_time < h2_2026_split]
    h2_idx = [i for i, b in enumerate(full_bos) if b.bos_time >= h2_2026_split]

    h1_bos = [full_bos[i] for i in h1_idx]
    h1_ob = [full_ob[i] for i in h1_idx]
    h1_gen = [full_gen[i] for i in h1_idx]

    h2_bos = [full_bos[i] for i in h2_idx]
    h2_ob = [full_ob[i] for i in h2_idx]
    h2_gen = [full_gen[i] for i in h2_idx]

    period_full = _aggregate_period(
        full_bos, full_ob, full_gen,
        period_label="full",
        family_size=family_size,
        n_min=n_min,
        delta_floor_pp=delta_floor_pp,
        alpha=alpha,
    )
    period_h1 = _aggregate_period(
        h1_bos, h1_ob, h1_gen,
        period_label="H1_2026",
        family_size=family_size,
        n_min=n_min,
        delta_floor_pp=delta_floor_pp,
        alpha=alpha,
    )
    period_h2 = _aggregate_period(
        h2_bos, h2_ob, h2_gen,
        period_label="H2_2026",
        family_size=family_size,
        n_min=n_min,
        delta_floor_pp=delta_floor_pp,
        alpha=alpha,
    )

    report = TestAReport(
        harness_version=HARNESS_VERSION,
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        instruments=tuple(instruments),
        family_size=family_size,
        n_bos_total=len(full_bos),
        period_full=period_full,
        period_h1=period_h1,
        period_h2=period_h2,
        per_instrument=per_instrument,
        n_min_floor=n_min,
        delta_floor_pp=delta_floor_pp,
        alpha=alpha,
    )
    return report, full_bos, full_ob, full_gen


# ---------------------------------------------------------------------------
# JSON-safe serialization
# ---------------------------------------------------------------------------


def _serialize_bos(bos: BOSEvent) -> dict:
    d = asdict(bos)
    for key in ("bos_time", "swing_time", "anchor_swing_time", "ob_time"):
        v = d.get(key)
        if isinstance(v, dt.datetime):
            d[key] = v.isoformat()
    return d


def _serialize_outcome(o: Outcome) -> dict:
    return asdict(o)


def serialize_population(
    bos_events: Sequence[BOSEvent],
    ob_outcomes: Sequence[Outcome],
    generic_outcomes: Sequence[Outcome],
) -> List[dict]:
    """Build a list of population.jsonl rows pairing each BOS with both
    strategy outcomes.
    """
    out: List[dict] = []
    for b, ob_o, gen_o in zip(bos_events, ob_outcomes, generic_outcomes):
        out.append({
            "bos": _serialize_bos(b),
            "ob_retest": _serialize_outcome(ob_o),
            "generic_50pct": _serialize_outcome(gen_o),
        })
    return out


def serialize_report(report: TestAReport) -> dict:
    """Convert TestAReport to a JSON-safe dict."""
    d = asdict(report)
    return _replace_nan(d)


def _replace_nan(obj: Any) -> Any:
    """Recursively replace NaN / Inf with None for JSON serialization."""
    if isinstance(obj, float):
        if not math.isfinite(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _replace_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_nan(v) for v in obj]
    if isinstance(obj, tuple):
        return [_replace_nan(v) for v in obj]
    return obj
