#!/usr/bin/env python3
"""GTOS Retest Geometry Study — CORRECTED (ADR 003) twin-geometry rerun.

Purpose
-------
Characterize the geometry of OB retests under **two** parallel outcome
classifications per retest:

- **Geometry A** — ADR 002 spirit (wider SL via ATR buffer, 1 OB-body target,
  12-h window). Clean theoretical baseline.
- **Geometry B** — Test A calibration (tight percentage SL buffer, 1.5R
  target, 3-h window). Matches ``scripts/ob_retest_comprehensive.py`` so
  the headline rate can be compared to the n=219 +17pp baseline.

What ADR 003 corrects
---------------------
v1 walked M15 forward from ``ob.formation_time`` (= open time of the H1
opposing candle BEFORE the BOS). That meant the "first retest" always
landed 15 minutes later — INSIDE the impulse candle that retroactively
creates the OB once the BOS confirms. Every v1 row had
``retest_ts = ob_formation_ts + 15 min``. That is look-ahead, not retest.

v2 walks M15 forward only from the first candle whose open is strictly
greater than or equal to the **close** of the BOS-confirming H1 candle
(``bos_confirm_ts``). A mandatory temporal-ordering invariant
(``retest_ts > bos_confirm_ts``) is enforced at classification time and
re-verified by a full-CSV unit test.

Ports
-----
OB detection (per-date 168 H1 lookback, dedup on
``(formation_time, type, high, low)``) is inherited unchanged from v1.
A3 signed off on that piece. The new piece is the ``bos_confirm_ts``
capture plus the corrected retest walk.

Per-retest CSV schema (twin geometry — 34 columns)
--------------------------------------------------
symbol, ob_formation_ts, bos_confirm_ts, retest_ts, retest_date, session,
side, ob_body_size_pips, ob_body_size_atr, ob_body_size_pct_price,
retest_entry_price, h1_atr_at_retest,
# Geometry A
sl_a_price, target_a_price, outcome_a, continuation_r_a,
mae_a_pips, mae_a_atr, mae_a_pct_ob_body,
penetration_a_pips, penetration_a_atr,
time_to_mae_a_candles, time_to_continuation_a_candles,
# Geometry B (Test A)
sl_b_price, target_b_price, outcome_b, continuation_r_b,
mae_b_pips, mae_b_atr, mae_b_pct_ob_body,
penetration_b_pips, penetration_b_atr,
time_to_mae_b_candles, time_to_continuation_b_candles

CLI
---
    python research/retest_geometry/study.py \\
        --symbols XAUUSD,US30_cash,USDJPY,GBPJPY,GBPUSD \\
        --start 2026-01-01 --end 2026-04-17 \\
        --report both

Test-isolation discipline
-------------------------
All paths are module-level constants. Tests monkeypatch via
``from research.retest_geometry import study as _mod`` +
``monkeypatch.setattr(_mod, "OUT_DIR", tmp_path)``.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
from dataclasses import dataclass, field, fields as dc_fields
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Optional

# ---------------------------------------------------------------------------
# Project-root importability
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Production imports — import failures must be caught so tests can still
# import this module with mocked primitives.
# ---------------------------------------------------------------------------
try:
    from scripts.historical_data_loader import parse_tradingview_csv
    from src.components.market_state import (
        calculate_atr,
        detect_structure_breaks,
        detect_swings,
        identify_order_blocks,
        identify_structure,
    )
    from src.utils.time_utils import get_current_session
except Exception as exc:  # pragma: no cover — import handled in main
    parse_tradingview_csv = None  # type: ignore[assignment]
    calculate_atr = None  # type: ignore[assignment]
    detect_structure_breaks = None  # type: ignore[assignment]
    detect_swings = None  # type: ignore[assignment]
    identify_order_blocks = None  # type: ignore[assignment]
    identify_structure = None  # type: ignore[assignment]
    get_current_session = None  # type: ignore[assignment]
    _IMPORT_ERROR: Optional[Exception] = exc
else:
    _IMPORT_ERROR = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module constants — tests MUST monkeypatch these on the module object.
# ---------------------------------------------------------------------------

DATA_DIR: Path = _PROJECT_ROOT / "data" / "historical"
OUT_DIR: Path = _PROJECT_ROOT / "research" / "retest_geometry" / "outputs"

SYMBOLS: list[str] = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]

# H1 lookback for per-date OB detection. Mirrors
# ``scripts/historical_data_loader.LOOKBACK["H1"]`` = 168 (~7 days).
H1_LOOKBACK: int = 168

# M15 retest forward scan window (192 candles = 48h).
RETEST_SCAN_WINDOW: int = 192

# Geometry A: resolution horizon (48 M15 candles = 12h) per ADR 002 spirit.
RESOLUTION_HORIZON_A: int = 48
# Geometry B (Test A): resolution horizon (12 M15 candles = 3h).
# Extracted from ``scripts/ob_retest_comprehensive.py`` line 537 ``for j in range(1, 13)``.
RESOLUTION_HORIZON_B: int = 12

# Geometry B target multiplier (Test A).
# Extracted from ``scripts/ob_retest_comprehensive.py`` line 531
# ``target_distance = 1.5 * sl_distance``.
GEOMETRY_B_TARGET_R: float = 1.5

# Live-period boundary per ADR 002.
LIVE_PERIOD_START: date = date(2026, 4, 7)

# Live-system record roots (for the live-period join).
LIVE_EVALUATIONS_DIR: Path = _PROJECT_ROOT / "knowledge_base" / "live_evaluations"
TRADE_RECORDS_DIR: Path = _PROJECT_ROOT / "knowledge_base" / "trade_records"
NO_TRADES_DIR: Path = _PROJECT_ROOT / "knowledge_base" / "no_trades"

# ATR normalization period.
ATR_PERIOD: int = 14

# Geometry A SL buffer in H1 ATR units. Per ADR 002 / 003: 0.5 × H1 ATR(14) at retest.
SL_MARGIN_ATR_A: float = 0.5

# Geometry B SL buffer — extracted from ``scripts/ob_retest_comprehensive.py``
# lines 432-435, 462-465:
#   XAUUSD: ``ob_low - 0.001 * ob_low`` (0.1% of price, e.g. ~$4.40 at $4400)
#   Other:  ``ob_low - 0.00015`` (absolute 0.00015 price units)
# This is what Test A literally uses; reproducing verbatim for comparability.
# Note: for JPY pairs and indices (US30) the 0.00015 absolute buffer is
# microscopic relative to price — we still use it to stay faithful to Test A
# and flag the caveat in the report.
GEOMETRY_B_SL_XAUUSD_PCT: float = 0.001  # 0.1% of OB edge price
GEOMETRY_B_SL_OTHER_ABS: float = 0.00015  # absolute price units

# Per-symbol pip size (for pip conversion in the output). Using MT5
# conventions: JPY pairs 0.01 per pip, FX 0.0001, index 1.0, gold 0.1.
SYMBOL_PIP_SIZE: dict[str, float] = {
    "XAUUSD": 0.1,       # 1 pip = $0.1 (gold)
    "US30_cash": 1.0,    # 1 pip = 1 index point
    "USDJPY": 0.01,      # JPY
    "GBPJPY": 0.01,      # JPY
    "GBPUSD": 0.0001,    # FX
}

# H1 candle duration (for bos_confirm_ts derivation).
H1_DURATION = timedelta(hours=1)


# ---------------------------------------------------------------------------
# Session label helper — collapse production labels to study labels
# ---------------------------------------------------------------------------

def session_label(dt_utc: datetime) -> str:
    """Return one of 'London' / 'NY' / 'Tokyo' / 'None' for a UTC datetime.

    The production ``get_current_session`` returns 6 fine-grained labels plus
    ``off_hours``. For the study we collapse:
        london_open, london_body  → "London"
        ny_overlap, ny_open, ny_afternoon → "NY"
        asian → "Tokyo"
        off_hours → "None"
    """
    if get_current_session is None:  # pragma: no cover
        return "None"
    prod_label = get_current_session(dt_utc)
    if prod_label in ("london_open", "london_body"):
        return "London"
    if prod_label in ("ny_overlap", "ny_open", "ny_afternoon"):
        return "NY"
    if prod_label == "asian":
        return "Tokyo"
    return "None"


# ---------------------------------------------------------------------------
# Data classes — v2 twin-geometry schema
# ---------------------------------------------------------------------------

RetestOutcome = Literal["CONTINUED", "REVERSED", "UNRESOLVED"]


@dataclass(frozen=True)
class RetestRecord:
    """Per-retest row — maps 1:1 to output CSV columns.

    Twin-geometry v2 schema: 34 columns (12 common + 11 Geom A + 11 Geom B).
    Column order MUST match ADR 003. Tests verify ``CSV_FIELDS`` derivation
    from this dataclass preserves that order.
    """
    symbol: str
    ob_formation_ts: str               # ISO 8601 UTC — H1 opposing candle open
    bos_confirm_ts: str                # ISO 8601 UTC — BOS-confirming H1 candle CLOSE
    retest_ts: str                     # ISO 8601 UTC — first M15 after bos_confirm_ts entering zone
    retest_date: str                   # YYYY-MM-DD (UTC)
    session: str                       # London/NY/Tokyo/None
    side: str                          # long/short
    ob_body_size_pips: float
    ob_body_size_atr: float
    ob_body_size_pct_price: float
    retest_entry_price: float
    h1_atr_at_retest: float
    # Geometry A
    sl_a_price: float
    target_a_price: float
    outcome_a: str                     # CONTINUED/REVERSED/UNRESOLVED
    continuation_r_a: Optional[float]
    mae_a_pips: float
    mae_a_atr: float
    mae_a_pct_ob_body: float
    penetration_a_pips: float
    penetration_a_atr: float
    time_to_mae_a_candles: int
    time_to_continuation_a_candles: Optional[int]
    # Geometry B (Test A)
    sl_b_price: float
    target_b_price: float
    outcome_b: str
    continuation_r_b: Optional[float]
    mae_b_pips: float
    mae_b_atr: float
    mae_b_pct_ob_body: float
    penetration_b_pips: float
    penetration_b_atr: float
    time_to_mae_b_candles: int
    time_to_continuation_b_candles: Optional[int]


# Derive CSV column order once; tests verify this matches the dataclass.
CSV_FIELDS: list[str] = [f.name for f in dc_fields(RetestRecord)]


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _parse_candle_time(t: str) -> datetime:
    """Parse candle timestamp to UTC datetime.

    Accepts the formats emitted by ``historical_data_loader.parse_tradingview_csv``
    (``YYYY-MM-DDTHH:MM:SSZ``) plus legacy local formats. Returns a tz-aware
    UTC datetime.
    """
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse candle time: {t!r}")


def _utc_date(t: str) -> date:
    """Extract the UTC date component from a candle time string."""
    return _parse_candle_time(t).date()


def _format_utc_iso(dt: datetime) -> str:
    """Format a UTC datetime in the canonical ``YYYY-MM-DDTHH:MM:SSZ`` form."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pip_size_for(symbol: str) -> float:
    """Return pip size for the symbol. Defaults to 0.0001 for unknown."""
    return SYMBOL_PIP_SIZE.get(symbol, 0.0001)


def _safe_div(numerator: float, denominator: float) -> float:
    """Safe division — returns 0.0 on zero denominator."""
    if denominator == 0 or denominator == 0.0:
        return 0.0
    return numerator / denominator


# ---------------------------------------------------------------------------
# Annotated OB with bos_confirm_ts — v2 augmentation over plain production OB
# ---------------------------------------------------------------------------


@dataclass
class AnnotatedOB:
    """Production ``OrderBlock`` plus its BOS-confirmation close timestamp.

    ``bos_confirm_ts`` is derived from ``ob.causing_bos_index`` plus the H1
    slice that produced the OB:
        bos_confirm_ts = parse(h1_slice[causing_bos_index].time) + 1h

    This is the timestamp at which the BOS candle *closed* — the first moment
    at which the OB is structurally defined. The retest walk must start
    strictly after this time.
    """
    ob: Any                    # production OrderBlock
    bos_confirm_ts: str        # ISO 8601 UTC


# ---------------------------------------------------------------------------
# Per-date OB detection (mirrors ``ob_retest_comprehensive.py`` approach)
# ---------------------------------------------------------------------------


def _index_by_date(candles: list[dict]) -> dict[date, list[int]]:
    """Map each UTC date to indices in the candle list."""
    idx: dict[date, list[int]] = {}
    for i, c in enumerate(candles):
        try:
            d = _utc_date(c["time"])
        except (KeyError, ValueError):
            continue
        idx.setdefault(d, []).append(i)
    return idx


def _get_lookback_slice(
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
    target_date: date,
    lookback: int,
) -> list[dict]:
    """Return the H1 lookback slice ending at the last H1 candle of target_date."""
    if target_date not in h1_date_idx:
        return []
    last_idx = h1_date_idx[target_date][-1]
    start_idx = max(0, last_idx - lookback + 1)
    return h1_candles[start_idx : last_idx + 1]


def detect_fresh_obs_on_date(
    target_date: date,
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
) -> list[AnnotatedOB]:
    """Detect H1 OBs visible on ``target_date`` using a 168-candle lookback.

    Returns a list of ``AnnotatedOB`` (production OB + ``bos_confirm_ts``).
    Only fresh (unmitigated-as-of-target_date) OBs are returned. Mirrors the
    per-date detection pattern of ``ob_retest_comprehensive.compute_obs_for_date``.

    ``bos_confirm_ts`` is the CLOSE timestamp of the BOS candle that confirms
    the OB — derived from ``ob.causing_bos_index`` within the produced slice.
    """
    if detect_swings is None:
        logger.error("Production primitives unavailable")
        return []

    h1_slice = _get_lookback_slice(h1_candles, h1_date_idx, target_date, H1_LOOKBACK)
    if len(h1_slice) < 20:
        return []

    swings = detect_swings(h1_slice)
    structure = identify_structure(swings)
    events = detect_structure_breaks(h1_slice, swings, structure)
    obs = identify_order_blocks(h1_slice, events)
    annotated: list[AnnotatedOB] = []
    for ob in obs:
        if getattr(ob, "mitigated", True):
            continue
        bos_idx = getattr(ob, "causing_bos_index", None)
        if bos_idx is None or bos_idx < 0 or bos_idx >= len(h1_slice):
            # Should not happen with production detection — skip defensively
            continue
        try:
            bos_open_dt = _parse_candle_time(h1_slice[bos_idx]["time"])
        except (KeyError, ValueError):
            continue
        # BOS confirms at the CLOSE of its H1 candle (open + 1h)
        bos_close_dt = bos_open_dt + H1_DURATION
        annotated.append(AnnotatedOB(
            ob=ob,
            bos_confirm_ts=_format_utc_iso(bos_close_dt),
        ))
    return annotated


def collect_unique_fresh_obs(
    h1_candles: list[dict],
    start_date: date,
    end_date: date,
) -> list[AnnotatedOB]:
    """Walk each date in [start_date, end_date]; accumulate unique fresh OBs.

    Each OB is identified by
    ``(formation_time, type, high, low)``. The FIRST appearance wins — i.e.,
    the OB is captured on the first date where production detection saw it
    as fresh. The ``bos_confirm_ts`` from that first appearance is kept.

    Returns annotated OBs sorted ascending by formation_time.
    """
    h1_date_idx = _index_by_date(h1_candles)
    seen: set[tuple] = set()
    uniques: list[AnnotatedOB] = []

    cur = start_date
    while cur <= end_date:
        fresh = detect_fresh_obs_on_date(cur, h1_candles, h1_date_idx)
        for aob in fresh:
            ob = aob.ob
            key = (
                getattr(ob, "formation_time", None),
                getattr(ob, "type", None),
                round(float(getattr(ob, "high", 0.0)), 8),
                round(float(getattr(ob, "low", 0.0)), 8),
            )
            if key in seen:
                continue
            seen.add(key)
            uniques.append(aob)
        cur = cur + timedelta(days=1)

    uniques.sort(key=lambda a: _parse_candle_time(getattr(a.ob, "formation_time")))
    return uniques


# ---------------------------------------------------------------------------
# CORRECTED retest detection — walk M15 forward from bos_confirm_ts
# ---------------------------------------------------------------------------


@dataclass
class _RawRetest:
    """Intermediate retest record pre-geometry measurement."""
    ob: Any
    bos_confirm_ts: str
    retest_ts: str
    retest_idx: int
    entry_price: float
    entry_idx: int
    h1_atr: float


def _find_h1_atr_at(h1_candles: list[dict], target_time: datetime) -> float:
    """Return H1 ATR(14) computed over the most recent H1 candles strictly
    before ``target_time``. Uses production ``calculate_atr``.

    Returns 0.0 if fewer than 15 candles are available.
    """
    if calculate_atr is None:  # pragma: no cover
        return 0.0
    trailing: list[dict] = []
    for c in h1_candles:
        try:
            ct = _parse_candle_time(c["time"])
        except ValueError:
            continue
        if ct < target_time:
            trailing.append(c)
        else:
            break
    if len(trailing) < ATR_PERIOD + 1:
        return 0.0
    trailing = trailing[-(ATR_PERIOD * 4) :]
    return calculate_atr(trailing, ATR_PERIOD)


def _detect_first_retest(
    aob: AnnotatedOB,
    m15_candles: list[dict],
) -> Optional[_RawRetest]:
    """Walk M15 forward from the BOS-confirmation close; return first retest.

    CORRECTED retest definition (ADR 003 Step 3):
    * The retest candle must have ``open >= bos_confirm_ts``.
    * Bullish OB: candle low enters the zone body
      (``ob.low <= candle.low <= ob.high``) OR wick pierces through from above
      (``candle.low < ob.low AND candle.high >= ob.low``).
    * Bearish OB: candle high enters the zone body OR wick pierces from below.

    Entry price mirrors ``ob_retest_comprehensive.py``: candle.close if inside
    zone, else next-candle open.

    Scans up to ``RETEST_SCAN_WINDOW`` (192 M15 candles = 48h) from
    ``bos_confirm_ts``.
    """
    ob = aob.ob
    ob_type = getattr(ob, "type", None)
    if ob_type not in ("bullish", "bearish"):
        return None

    try:
        bos_confirm_dt = _parse_candle_time(aob.bos_confirm_ts)
    except ValueError:
        return None

    ob_high = float(getattr(ob, "high"))
    ob_low = float(getattr(ob, "low"))

    # First M15 candle whose OPEN is STRICTLY > bos_confirm_ts.
    # ADR 003 enforces a strict temporal-ordering invariant
    # (``retest_ts > bos_confirm_ts``). Because bos_confirm_ts (=H1 close) is
    # always M15-boundary aligned, an M15 candle with open EQUAL to
    # bos_confirm_ts is the very first candle of the BOS-impulse continuation,
    # not a genuine retest. Skipping it preserves the invariant.
    start_idx: Optional[int] = None
    for i, c in enumerate(m15_candles):
        try:
            ct = _parse_candle_time(c["time"])
        except ValueError:
            continue
        if ct > bos_confirm_dt:
            start_idx = i
            break
    if start_idx is None:
        return None

    end_idx = min(start_idx + RETEST_SCAN_WINDOW, len(m15_candles))

    for i in range(start_idx, end_idx):
        c = m15_candles[i]
        low = float(c["low"])
        high = float(c["high"])

        if ob_type == "bullish":
            enters = low <= ob_high and low >= ob_low
            if not enters:
                # Wick pierced below the zone from above
                enters = low < ob_low and high >= ob_low
        else:  # bearish
            enters = high >= ob_low and high <= ob_high
            if not enters:
                # Wick pierced above the zone from below
                enters = high > ob_high and low <= ob_high

        if not enters:
            continue

        # Entry selection (mirrors ob_retest_comprehensive.py)
        if ob_type == "bullish":
            if c["close"] >= ob_low:
                entry_price = float(c["close"])
                entry_idx = i
            elif i + 1 < len(m15_candles):
                entry_price = float(m15_candles[i + 1]["open"])
                entry_idx = i + 1
            else:
                return None
        else:
            if c["close"] <= ob_high:
                entry_price = float(c["close"])
                entry_idx = i
            elif i + 1 < len(m15_candles):
                entry_price = float(m15_candles[i + 1]["open"])
                entry_idx = i + 1
            else:
                return None

        return _RawRetest(
            ob=ob,
            bos_confirm_ts=aob.bos_confirm_ts,
            retest_ts=c["time"],
            retest_idx=i,
            entry_price=entry_price,
            entry_idx=entry_idx,
            h1_atr=0.0,  # filled later
        )

    return None


# ---------------------------------------------------------------------------
# Twin-geometry classifier — measures both geometries over their own windows
# ---------------------------------------------------------------------------


def _geometry_b_sl_price(symbol: str, ob_type: str, ob_high: float, ob_low: float) -> float:
    """Return the Geometry B (Test A) SL price for a given OB edge.

    Extracted from ``scripts/ob_retest_comprehensive.py`` lines 432-435, 462-465.
    """
    if ob_type == "bullish":
        if symbol == "XAUUSD":
            return ob_low - GEOMETRY_B_SL_XAUUSD_PCT * ob_low
        return ob_low - GEOMETRY_B_SL_OTHER_ABS
    # bearish
    if symbol == "XAUUSD":
        return ob_high + GEOMETRY_B_SL_XAUUSD_PCT * ob_high
    return ob_high + GEOMETRY_B_SL_OTHER_ABS


@dataclass
class _GeometryResult:
    """Per-geometry measurement result."""
    outcome: RetestOutcome
    continuation_r: Optional[float]
    mae_value: float           # absolute price units
    time_to_mae: int
    penetration_value: float   # absolute price units
    time_to_continuation: Optional[int]


def _walk_and_classify(
    ob_type: str,
    entry_price: float,
    entry_idx: int,
    sl_price: float,
    target_price: float,
    ob_high: float,
    ob_low: float,
    ob_body_size: float,
    horizon: int,
    m15_candles: list[dict],
) -> _GeometryResult:
    """Walk forward ``horizon`` M15 candles from ``entry_idx``; classify.

    Returns a ``_GeometryResult`` with outcome, R, MAE, penetration, times.

    Semantics match the v1 classifier:
    * Entry candle (j=0) counts toward MAE / penetration but NOT toward
      SL/target hit (skip-entry-candle rule mirrors ``ob_retest_comprehensive.py``).
    * Ambiguous same-candle SL+TP uses open-price tiebreak (conservative default
      to REVERSED on true ambiguity).
    * CONTINUED / REVERSED classifications require an EXPLICIT target/SL hit
      within ``horizon``. Horizon expiry → UNRESOLVED.
    * Insufficient forward candles (< horizon + 1) → UNRESOLVED.
    """
    # Window: entry candle + horizon forward candles
    window_end = min(entry_idx + horizon + 1, len(m15_candles))
    forward = m15_candles[entry_idx : window_end]

    mae_value = 0.0
    time_to_mae = 0
    penetration_value = 0.0
    outcome: RetestOutcome = "UNRESOLVED"
    time_to_continuation: Optional[int] = None
    continuation_r: Optional[float] = None
    hit = False  # explicit flag so we don't mis-attribute "end of loop" to unresolved after a hit

    for j in range(0, len(forward)):
        c = forward[j]
        low = float(c["low"])
        high = float(c["high"])

        if ob_type == "bullish":
            adverse = entry_price - low
            if adverse > mae_value:
                mae_value = adverse
                time_to_mae = j
            if low < ob_low:
                pen = ob_low - low
                if pen > penetration_value:
                    penetration_value = pen

            if j >= 1:
                sl_hit = low <= sl_price
                tp_hit = high >= target_price
                if sl_hit and tp_hit:
                    o = float(c["open"])
                    if o <= sl_price:
                        outcome = "REVERSED"
                        hit = True
                        break
                    elif o >= target_price:
                        outcome = "CONTINUED"
                        time_to_continuation = j
                        if ob_body_size > 0:
                            continuation_r = (high - entry_price) / ob_body_size
                        hit = True
                        break
                    else:
                        outcome = "REVERSED"
                        hit = True
                        break
                elif sl_hit:
                    outcome = "REVERSED"
                    hit = True
                    break
                elif tp_hit:
                    outcome = "CONTINUED"
                    time_to_continuation = j
                    if ob_body_size > 0:
                        continuation_r = (high - entry_price) / ob_body_size
                    hit = True
                    break
        else:  # bearish
            adverse = high - entry_price
            if adverse > mae_value:
                mae_value = adverse
                time_to_mae = j
            if high > ob_high:
                pen = high - ob_high
                if pen > penetration_value:
                    penetration_value = pen

            if j >= 1:
                sl_hit = high >= sl_price
                tp_hit = low <= target_price
                if sl_hit and tp_hit:
                    o = float(c["open"])
                    if o >= sl_price:
                        outcome = "REVERSED"
                        hit = True
                        break
                    elif o <= target_price:
                        outcome = "CONTINUED"
                        time_to_continuation = j
                        if ob_body_size > 0:
                            continuation_r = (entry_price - low) / ob_body_size
                        hit = True
                        break
                    else:
                        outcome = "REVERSED"
                        hit = True
                        break
                elif sl_hit:
                    outcome = "REVERSED"
                    hit = True
                    break
                elif tp_hit:
                    outcome = "CONTINUED"
                    time_to_continuation = j
                    if ob_body_size > 0:
                        continuation_r = (entry_price - low) / ob_body_size
                    hit = True
                    break

    if not hit:
        # Loop completed without SL or target hit. Whether the horizon was
        # fully available or truncated, the outcome is UNRESOLVED.
        outcome = "UNRESOLVED"

    return _GeometryResult(
        outcome=outcome,
        continuation_r=continuation_r,
        mae_value=mae_value,
        time_to_mae=time_to_mae,
        penetration_value=penetration_value,
        time_to_continuation=time_to_continuation,
    )


def _classify_and_measure(
    raw: _RawRetest,
    m15_candles: list[dict],
    symbol: str,
) -> RetestRecord:
    """Twin-geometry classify + measure. Returns a full RetestRecord.

    Enforces the ADR 003 temporal-ordering invariant:
    ``retest_ts > bos_confirm_ts`` (strict). Raises ``AssertionError`` if
    the invariant is violated — the test suite treats this as a release blocker.
    """
    ob = raw.ob
    ob_type = getattr(ob, "type")
    side = "long" if ob_type == "bullish" else "short"
    ob_high = float(getattr(ob, "high"))
    ob_low = float(getattr(ob, "low"))
    entry_price = raw.entry_price
    entry_idx = raw.entry_idx
    h1_atr = raw.h1_atr if raw.h1_atr > 0 else 1e-9

    ob_body_size = max(ob_high - ob_low, 1e-9)
    pip = pip_size_for(symbol)

    # --- Temporal-ordering invariant (ADR 003 MANDATORY) ---
    retest_dt = _parse_candle_time(raw.retest_ts)
    bos_dt = _parse_candle_time(raw.bos_confirm_ts)
    assert retest_dt > bos_dt, (
        f"Temporal invariant violated: retest_ts={raw.retest_ts} "
        f"<= bos_confirm_ts={raw.bos_confirm_ts}"
    )

    # --- Geometry A (ADR 002 spirit) ---
    if ob_type == "bullish":
        sl_a = ob_low - SL_MARGIN_ATR_A * h1_atr
        target_a = entry_price + ob_body_size
    else:
        sl_a = ob_high + SL_MARGIN_ATR_A * h1_atr
        target_a = entry_price - ob_body_size

    ga = _walk_and_classify(
        ob_type=ob_type, entry_price=entry_price, entry_idx=entry_idx,
        sl_price=sl_a, target_price=target_a,
        ob_high=ob_high, ob_low=ob_low, ob_body_size=ob_body_size,
        horizon=RESOLUTION_HORIZON_A,
        m15_candles=m15_candles,
    )

    # --- Geometry B (Test A) ---
    sl_b = _geometry_b_sl_price(symbol, ob_type, ob_high, ob_low)
    sl_b_distance = abs(entry_price - sl_b)
    if ob_type == "bullish":
        target_b = entry_price + GEOMETRY_B_TARGET_R * sl_b_distance
    else:
        target_b = entry_price - GEOMETRY_B_TARGET_R * sl_b_distance

    # Geom B continuation_r is expressed in R-units relative to SL distance
    # (because target = 1.5R is defined in SL-distance units). However, per
    # brief Step 4 we keep the same schema shape — continuation_r_b is also
    # ob_body normalized for consistency with A. Decision preserved below.
    gb = _walk_and_classify(
        ob_type=ob_type, entry_price=entry_price, entry_idx=entry_idx,
        sl_price=sl_b, target_price=target_b,
        ob_high=ob_high, ob_low=ob_low, ob_body_size=ob_body_size,
        horizon=RESOLUTION_HORIZON_B,
        m15_candles=m15_candles,
    )

    return RetestRecord(
        symbol=symbol,
        ob_formation_ts=getattr(ob, "formation_time"),
        bos_confirm_ts=raw.bos_confirm_ts,
        retest_ts=raw.retest_ts,
        retest_date=retest_dt.date().isoformat(),
        session=session_label(retest_dt),
        side=side,
        ob_body_size_pips=round(ob_body_size / pip, 4),
        ob_body_size_atr=round(_safe_div(ob_body_size, h1_atr), 4),
        ob_body_size_pct_price=round(_safe_div(ob_body_size, entry_price) * 100.0, 6),
        retest_entry_price=round(entry_price, 5),
        h1_atr_at_retest=round(h1_atr if raw.h1_atr > 0 else 0.0, 6),
        # Geometry A
        sl_a_price=round(sl_a, 5),
        target_a_price=round(target_a, 5),
        outcome_a=ga.outcome,
        continuation_r_a=round(ga.continuation_r, 4) if ga.continuation_r is not None else None,
        mae_a_pips=round(ga.mae_value / pip, 4),
        mae_a_atr=round(_safe_div(ga.mae_value, h1_atr), 4),
        mae_a_pct_ob_body=round(_safe_div(ga.mae_value, ob_body_size) * 100.0, 4),
        penetration_a_pips=round(ga.penetration_value / pip, 4),
        penetration_a_atr=round(_safe_div(ga.penetration_value, h1_atr), 4),
        time_to_mae_a_candles=int(ga.time_to_mae),
        time_to_continuation_a_candles=ga.time_to_continuation,
        # Geometry B
        sl_b_price=round(sl_b, 5),
        target_b_price=round(target_b, 5),
        outcome_b=gb.outcome,
        continuation_r_b=round(gb.continuation_r, 4) if gb.continuation_r is not None else None,
        mae_b_pips=round(gb.mae_value / pip, 4),
        mae_b_atr=round(_safe_div(gb.mae_value, h1_atr), 4),
        mae_b_pct_ob_body=round(_safe_div(gb.mae_value, ob_body_size) * 100.0, 4),
        penetration_b_pips=round(gb.penetration_value / pip, 4),
        penetration_b_atr=round(_safe_div(gb.penetration_value, h1_atr), 4),
        time_to_mae_b_candles=int(gb.time_to_mae),
        time_to_continuation_b_candles=gb.time_to_continuation,
    )


# ---------------------------------------------------------------------------
# Per-symbol pipeline
# ---------------------------------------------------------------------------


def _load_csv(path: Path) -> list[dict]:
    """Load a candles CSV. Returns [] on any failure."""
    if parse_tradingview_csv is None:
        raise RuntimeError(f"parse_tradingview_csv unavailable ({_IMPORT_ERROR})")
    if not path.exists():
        logger.warning("CSV missing: %s", path)
        return []
    try:
        return parse_tradingview_csv(path)
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", path, exc)
        return []


def _filter_by_date(candles: list[dict], start: date, end: date) -> list[dict]:
    """Return candles whose UTC date is within [start, end], inclusive.

    Keeps a small margin BEFORE start (for ATR and structure bootstrap) —
    specifically we return the full list truncated at end. Down-filtering
    of the start is done at retest-detection time so OBs formed before
    ``start`` but retested within the study window ARE captured.
    """
    out: list[dict] = []
    for c in candles:
        try:
            d = _utc_date(c["time"])
        except (KeyError, ValueError):
            continue
        if d > end:
            break
        out.append(c)
    return out


def build_retests_for_symbol(
    symbol: str,
    start_date: date,
    end_date: date,
    data_dir: Path,
) -> list[RetestRecord]:
    """Full per-symbol pipeline under corrected retest timing.

    1. Load M15 + H1 CSVs from ``data_dir``.
    2. Walk each date in [start_date, end_date]; detect fresh OBs with
       ``bos_confirm_ts`` annotated.
    3. For each unique fresh (annotated) OB, detect first retest on M15
       with ``retest_ts > bos_confirm_ts``.
    4. Compute H1 ATR at retest; measure twin geometry; classify outcomes.
    5. Return list of RetestRecord sorted ascending by (symbol, retest_ts).
    """
    h1_path = data_dir / f"{symbol}_H1.csv"
    m15_path = data_dir / f"{symbol}_M15.csv"

    h1_all = _load_csv(h1_path)
    m15_all = _load_csv(m15_path)
    if not h1_all or not m15_all:
        logger.warning("Missing data for %s (H1=%d, M15=%d) — skipping",
                       symbol, len(h1_all), len(m15_all))
        return []

    h1 = _filter_by_date(h1_all, date(1970, 1, 1), end_date)
    m15 = _filter_by_date(m15_all, date(1970, 1, 1), end_date)

    if len(h1) < H1_LOOKBACK or len(m15) < RESOLUTION_HORIZON_A:
        logger.warning("Too few candles for %s — H1=%d, M15=%d", symbol, len(h1), len(m15))
        return []

    logger.info("%s: H1=%d, M15=%d candles through %s",
                symbol, len(h1), len(m15), end_date)

    obs = collect_unique_fresh_obs(h1, start_date, end_date)
    logger.info("%s: %d unique fresh OBs in [%s, %s]",
                symbol, len(obs), start_date, end_date)

    results: list[RetestRecord] = []
    for aob in obs:
        raw = _detect_first_retest(aob, m15)
        if raw is None:
            continue

        retest_dt = _parse_candle_time(raw.retest_ts)
        retest_d = retest_dt.date()
        if retest_d < start_date or retest_d > end_date:
            continue

        raw.h1_atr = _find_h1_atr_at(h1, retest_dt)

        rec = _classify_and_measure(raw, m15, symbol)
        results.append(rec)

    results.sort(key=lambda r: (r.symbol, r.retest_ts))
    return results


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------


def _format_field(value: Any) -> str:
    """Format a single CSV field. None → empty string; floats use %.6g."""
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.6g}"
    return str(value)


def write_retest_csv(records: list[RetestRecord], out_path: Path) -> None:
    """Write retests to CSV with the canonical twin-geometry schema.

    Deterministic ordering: by (symbol, retest_ts) — caller guarantees this.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(CSV_FIELDS)
        for r in records:
            row = [_format_field(getattr(r, f)) for f in CSV_FIELDS]
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Analysis helpers (stats)
# ---------------------------------------------------------------------------


def _percentiles(values: list[float], pcts: Iterable[float]) -> dict[float, float]:
    """Compute percentiles with linear interpolation (type 7, numpy default).

    ``values`` need not be sorted. Returns dict keyed by percent (0-100).
    Empty input → all percentiles are NaN.
    """
    if not values:
        return {p: float("nan") for p in pcts}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    out: dict[float, float] = {}
    for p in pcts:
        if n == 1:
            out[p] = sorted_vals[0]
            continue
        rank = (p / 100.0) * (n - 1)
        lo = int(math.floor(rank))
        hi = int(math.ceil(rank))
        if lo == hi:
            out[p] = sorted_vals[lo]
        else:
            frac = rank - lo
            out[p] = sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])
    return out


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    phat = k / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return max(0.0, center - half), min(1.0, center + half)


def _tercile_boundaries(values: list[float]) -> tuple[float, float]:
    if len(values) < 3:
        return (float("nan"), float("nan"))
    pc = _percentiles(values, [33.333, 66.667])
    return (pc[33.333], pc[66.667])


def _tercile_label(v: float, low_cut: float, high_cut: float) -> str:
    if math.isnan(low_cut) or math.isnan(high_cut):
        return "mid"
    if v <= low_cut:
        return "low"
    if v <= high_cut:
        return "mid"
    return "high"


def outcome_breakdown(
    records: list[RetestRecord],
    geometry: str = "a",
) -> dict[str, int]:
    """Return outcome counts for the given geometry ('a' or 'b')."""
    attr = "outcome_a" if geometry == "a" else "outcome_b"
    out = {"CONTINUED": 0, "REVERSED": 0, "UNRESOLVED": 0, "total": 0}
    for r in records:
        out["total"] += 1
        v = getattr(r, attr)
        out[v] = out.get(v, 0) + 1
    return out


def continuation_rate(
    records: list[RetestRecord],
    geometry: str = "a",
    count_unresolved_as_no: bool = False,
) -> tuple[int, int, float]:
    """Return (continued, eligible, rate_pct) for the given geometry."""
    attr = "outcome_a" if geometry == "a" else "outcome_b"
    continued = sum(1 for r in records if getattr(r, attr) == "CONTINUED")
    if count_unresolved_as_no:
        eligible = len(records)
    else:
        eligible = sum(1 for r in records
                       if getattr(r, attr) in ("CONTINUED", "REVERSED"))
    if eligible == 0:
        return 0, 0, 0.0
    return continued, eligible, continued / eligible * 100.0


# ---------------------------------------------------------------------------
# Markdown report writer — historical (twin-geometry)
# ---------------------------------------------------------------------------


def _pct_table_row(label: str, values: list[float]) -> str:
    pc = _percentiles(values, [10, 25, 50, 75, 90])
    cells = []
    for p in (10, 25, 50, 75, 90):
        v = pc[p]
        cells.append(f"{v:.3f}" if not math.isnan(v) else "-")
    cells.insert(0, str(len(values)))
    cells.insert(0, label)
    return "| " + " | ".join(cells) + " |"


def _tercile_cont_rate_rows(
    records: list[RetestRecord],
    field_name: str,
    geometry: str,
) -> str:
    """Build 3 rows for a tercile continuation-rate table (per geometry)."""
    outcome_attr = "outcome_a" if geometry == "a" else "outcome_b"
    eligible = [r for r in records if getattr(r, outcome_attr) in ("CONTINUED", "REVERSED")]
    if not eligible:
        return "| (no data) | - | - | - | - |\n"
    values = [getattr(r, field_name) for r in eligible]
    low_cut, high_cut = _tercile_boundaries(values)

    buckets: dict[str, list[RetestRecord]] = {"low": [], "mid": [], "high": []}
    for r in eligible:
        label = _tercile_label(getattr(r, field_name), low_cut, high_cut)
        buckets[label].append(r)

    rows = []
    for label in ("low", "mid", "high"):
        bucket = buckets[label]
        continued = sum(1 for r in bucket if getattr(r, outcome_attr) == "CONTINUED")
        n = len(bucket)
        rate = continued / n * 100.0 if n else float("nan")
        lo, hi = _wilson_ci(continued, n) if n else (float("nan"), float("nan"))
        rate_str = f"{rate:.1f}%" if not math.isnan(rate) else "-"
        ci_str = (f"[{lo*100:.1f}%, {hi*100:.1f}%]"
                  if not math.isnan(lo) else "-")
        cut_str = "-"
        if label == "low":
            cut_str = (f"<= {low_cut:.3f}" if not math.isnan(low_cut) else "-")
        elif label == "mid":
            cut_str = (f"({low_cut:.3f}, {high_cut:.3f}]"
                       if not math.isnan(low_cut) else "-")
        else:
            cut_str = (f"> {high_cut:.3f}" if not math.isnan(high_cut) else "-")
        rows.append(f"| {label} | {cut_str} | {continued}/{n} | {rate_str} | {ci_str} |")
    return "\n".join(rows) + "\n"


def _session_breakdown_table(records: list[RetestRecord], geometry: str) -> str:
    """Continuation rate by session, per symbol + combined (per geometry)."""
    outcome_attr = "outcome_a" if geometry == "a" else "outcome_b"
    groups: dict[tuple[str, str], list[RetestRecord]] = {}
    all_symbols: set[str] = set()
    for r in records:
        groups.setdefault((r.symbol, r.session), []).append(r)
        all_symbols.add(r.symbol)

    ordered_sessions = ["London", "NY", "Tokyo", "None"]
    ordered_symbols = sorted(all_symbols)

    lines = ["| symbol | " + " | ".join(ordered_sessions) + " |"]
    lines.append("|" + "|".join(["---"] * (len(ordered_sessions) + 1)) + "|")

    for sym in ordered_symbols:
        cells = [sym]
        for sess in ordered_sessions:
            bucket = groups.get((sym, sess), [])
            eligible = [r for r in bucket if getattr(r, outcome_attr) in ("CONTINUED", "REVERSED")]
            if not eligible:
                cells.append("-")
                continue
            cont = sum(1 for r in eligible if getattr(r, outcome_attr) == "CONTINUED")
            rate = cont / len(eligible) * 100.0
            cells.append(f"{cont}/{len(eligible)} ({rate:.1f}%)")
        lines.append("| " + " | ".join(cells) + " |")

    cells = ["**all**"]
    for sess in ordered_sessions:
        bucket = [r for r in records if r.session == sess]
        eligible = [r for r in bucket if getattr(r, outcome_attr) in ("CONTINUED", "REVERSED")]
        if not eligible:
            cells.append("-")
            continue
        cont = sum(1 for r in eligible if getattr(r, outcome_attr) == "CONTINUED")
        rate = cont / len(eligible) * 100.0
        cells.append(f"{cont}/{len(eligible)} ({rate:.1f}%)")
    lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _summary_line(records: list[RetestRecord], geometry: str) -> str:
    """Per-symbol summary for the given geometry."""
    outcome_attr = "outcome_a" if geometry == "a" else "outcome_b"
    by_sym: dict[str, list[RetestRecord]] = {}
    for r in records:
        by_sym.setdefault(r.symbol, []).append(r)
    lines = ["| symbol | n | CONTINUED | REVERSED | UNRESOLVED | rate (ex-UNR) |"]
    lines.append("|---|---|---|---|---|---|")
    for sym in sorted(by_sym.keys()):
        recs = by_sym[sym]
        ob = outcome_breakdown(recs, geometry=geometry)
        _, _, rate = continuation_rate(recs, geometry=geometry)
        lines.append(
            f"| {sym} | {ob['total']} | {ob['CONTINUED']} | "
            f"{ob['REVERSED']} | {ob['UNRESOLVED']} | {rate:.1f}% |"
        )
    ob = outcome_breakdown(records, geometry=geometry)
    _, _, rate = continuation_rate(records, geometry=geometry)
    lines.append(
        f"| **combined** | {ob['total']} | {ob['CONTINUED']} | "
        f"{ob['REVERSED']} | {ob['UNRESOLVED']} | {rate:.1f}% |"
    )
    return "\n".join(lines) + "\n"


def _outcome_dist_table(records: list[RetestRecord], geometry: str) -> str:
    outcome_attr = "outcome_a" if geometry == "a" else "outcome_b"
    by_sym: dict[str, list[RetestRecord]] = {}
    for r in records:
        by_sym.setdefault(r.symbol, []).append(r)
    lines = ["| symbol | n | %CONTINUED | %REVERSED | %UNRESOLVED |"]
    lines.append("|---|---|---|---|---|")
    for sym in sorted(by_sym.keys()):
        recs = by_sym[sym]
        ob = outcome_breakdown(recs, geometry=geometry)
        n = ob["total"] or 1
        lines.append(
            f"| {sym} | {ob['total']} | "
            f"{ob['CONTINUED']/n*100:.1f}% | "
            f"{ob['REVERSED']/n*100:.1f}% | "
            f"{ob['UNRESOLVED']/n*100:.1f}% |"
        )
    ob = outcome_breakdown(records, geometry=geometry)
    n = ob["total"] or 1
    lines.append(
        f"| **combined** | {ob['total']} | "
        f"{ob['CONTINUED']/n*100:.1f}% | "
        f"{ob['REVERSED']/n*100:.1f}% | "
        f"{ob['UNRESOLVED']/n*100:.1f}% |"
    )
    return "\n".join(lines) + "\n"


def _mae_percentiles_section(records: list[RetestRecord], geometry: str) -> str:
    suffix = "a" if geometry == "a" else "b"
    by_sym: dict[str, list[RetestRecord]] = {}
    for r in records:
        by_sym.setdefault(r.symbol, []).append(r)

    parts = []
    for metric_label, field_name in (
        (f"MAE (pips) — Geometry {suffix.upper()}", f"mae_{suffix}_pips"),
        (f"MAE (H1 ATR units) — Geometry {suffix.upper()}", f"mae_{suffix}_atr"),
        (f"MAE (% of OB body) — Geometry {suffix.upper()}", f"mae_{suffix}_pct_ob_body"),
    ):
        parts.append(f"### {metric_label}\n")
        parts.append("| scope | n | p10 | p25 | p50 | p75 | p90 |")
        parts.append("|---|---|---|---|---|---|---|")
        for sym in sorted(by_sym.keys()):
            values = [getattr(r, field_name) for r in by_sym[sym]]
            parts.append(_pct_table_row(sym, values))
        parts.append(_pct_table_row("**combined**", [getattr(r, field_name) for r in records]))
        parts.append("")
    return "\n".join(parts) + "\n"


def _penetration_percentiles_section(records: list[RetestRecord], geometry: str) -> str:
    suffix = "a" if geometry == "a" else "b"
    by_sym: dict[str, list[RetestRecord]] = {}
    for r in records:
        by_sym.setdefault(r.symbol, []).append(r)
    parts = []
    for metric_label, field_name in (
        (f"Penetration (pips) — Geometry {suffix.upper()}", f"penetration_{suffix}_pips"),
        (f"Penetration (H1 ATR units) — Geometry {suffix.upper()}", f"penetration_{suffix}_atr"),
    ):
        parts.append(f"### {metric_label}\n")
        parts.append("| scope | n | p10 | p25 | p50 | p75 | p90 |")
        parts.append("|---|---|---|---|---|---|---|")
        for sym in sorted(by_sym.keys()):
            values = [getattr(r, field_name) for r in by_sym[sym]]
            parts.append(_pct_table_row(sym, values))
        parts.append(_pct_table_row("**combined**", [getattr(r, field_name) for r in records]))
        parts.append("")
    pen_pips_attr = f"penetration_{suffix}_pips"
    n = len(records)
    pierced = sum(1 for r in records if getattr(r, pen_pips_attr) > 0)
    pct = pierced / n * 100.0 if n else 0.0
    parts.append(f"**Fraction of retests that pierced the OB edge (Geometry {suffix.upper()}):** "
                 f"{pierced}/{n} = {pct:.1f}%\n")
    return "\n".join(parts) + "\n"


def _time_to_mae_section(records: list[RetestRecord], geometry: str) -> str:
    suffix = "a" if geometry == "a" else "b"
    field_name = f"time_to_mae_{suffix}_candles"
    values = [float(getattr(r, field_name)) for r in records]
    if not values:
        return "(no data)\n"
    pc = _percentiles(values, [10, 25, 50, 75, 90])
    parts = [
        f"**Percentiles (M15 candles from retest to MAE) — Geometry {suffix.upper()}:**",
        "",
        f"| p10 | p25 | p50 | p75 | p90 |",
        "|---|---|---|---|---|",
        "| " + " | ".join(f"{pc[p]:.1f}" for p in (10, 25, 50, 75, 90)) + " |",
    ]
    return "\n".join(parts) + "\n"


def _penetration_binary_table(records: list[RetestRecord], geometry: str) -> str:
    suffix = "a" if geometry == "a" else "b"
    pen_pips_attr = f"penetration_{suffix}_pips"
    outcome_attr = f"outcome_{suffix}"
    pierced = [r for r in records if getattr(r, pen_pips_attr) > 0
               and getattr(r, outcome_attr) in ("CONTINUED", "REVERSED")]
    not_pierced = [r for r in records if getattr(r, pen_pips_attr) == 0
                   and getattr(r, outcome_attr) in ("CONTINUED", "REVERSED")]

    def cell(bucket: list[RetestRecord]) -> str:
        n = len(bucket)
        if n == 0:
            return "-"
        cont = sum(1 for r in bucket if getattr(r, outcome_attr) == "CONTINUED")
        rate = cont / n * 100.0
        lo, hi = _wilson_ci(cont, n)
        return f"{cont}/{n} = {rate:.1f}% [{lo*100:.1f}%, {hi*100:.1f}%]"

    return (
        "| group | result |\n"
        "|---|---|\n"
        f"| pierced OB edge | {cell(pierced)} |\n"
        f"| did NOT pierce | {cell(not_pierced)} |\n"
    )


def _geometry_report_block(records: list[RetestRecord], geometry: str) -> str:
    """Full per-geometry analysis block."""
    suffix = "a" if geometry == "a" else "b"
    label = suffix.upper()
    sl_desc = (
        f"opposing side of OB + {SL_MARGIN_ATR_A} x H1 ATR(14) at retest"
        if geometry == "a"
        else f"Test A rule: XAUUSD `ob_low - {GEOMETRY_B_SL_XAUUSD_PCT} * ob_low` (bullish); "
             f"other symbols `ob_low - {GEOMETRY_B_SL_OTHER_ABS}` (absolute). "
             "Mirror for bearish."
    )
    target_desc = (
        "retest_entry + ob_body_size past far edge (1R = 1 OB body)"
        if geometry == "a"
        else f"retest_entry + {GEOMETRY_B_TARGET_R} x SL_distance"
    )
    horizon = RESOLUTION_HORIZON_A if geometry == "a" else RESOLUTION_HORIZON_B

    lines: list[str] = []
    lines.append(f"## Geometry {label}")
    lines.append("")
    lines.append(f"**SL:** {sl_desc}")
    lines.append(f"**Target:** {target_desc}")
    lines.append(f"**Resolution window:** {horizon} M15 candles ({horizon * 15 / 60:.1f}h)")
    lines.append("")
    lines.append(f"### Summary — retests per symbol (Geometry {label})")
    lines.append("")
    lines.append(_summary_line(records, geometry=geometry))
    lines.append("")
    lines.append(f"### Outcome distribution (Geometry {label})")
    lines.append("")
    lines.append(_outcome_dist_table(records, geometry=geometry))
    lines.append("")
    lines.append(f"### MAE percentiles (Geometry {label})")
    lines.append("")
    lines.append(_mae_percentiles_section(records, geometry=geometry))
    lines.append("")
    lines.append(f"### Penetration percentiles (Geometry {label})")
    lines.append("")
    lines.append(_penetration_percentiles_section(records, geometry=geometry))
    lines.append("")
    lines.append(f"### Time-to-MAE distribution (Geometry {label})")
    lines.append("")
    lines.append(_time_to_mae_section(records, geometry=geometry))
    lines.append("")
    lines.append(f"### Session breakdowns (Geometry {label})")
    lines.append("")
    lines.append("Continuation rate by session (CONTINUED / (CONTINUED+REVERSED)):")
    lines.append("")
    lines.append(_session_breakdown_table(records, geometry=geometry))
    lines.append("")
    lines.append(f"### MAE-tercile continuation (Geometry {label})")
    lines.append("")
    lines.append("Does deep MAE predict reversal?")
    lines.append("")
    lines.append("| tercile | MAE (ATR) range | continued/n | rate | 95% CI |")
    lines.append("|---|---|---|---|---|")
    lines.append(_tercile_cont_rate_rows(records, f"mae_{suffix}_atr", geometry=geometry))
    lines.append("")
    lines.append(f"### Penetration binary (Geometry {label})")
    lines.append("")
    lines.append(_penetration_binary_table(records, geometry=geometry))
    lines.append("")
    lines.append(f"### OB-body-size tercile continuation (Geometry {label})")
    lines.append("")
    lines.append("Do small / medium / large OBs differ?")
    lines.append("")
    lines.append("| tercile | body_size (ATR) range | continued/n | rate | 95% CI |")
    lines.append("|---|---|---|---|---|")
    lines.append(_tercile_cont_rate_rows(records, "ob_body_size_atr", geometry=geometry))
    lines.append("")
    return "\n".join(lines)


def build_historical_report_md(records: list[RetestRecord], run_meta: dict) -> str:
    """Build the twin-geometry historical report."""
    lines: list[str] = []
    lines.append("# Retest Geometry Study (v2, ADR 003) — Historical Report")
    lines.append("")
    lines.append(f"**Generated:** {run_meta['generated']}")
    lines.append(f"**Study window:** {run_meta['start']} -> {run_meta['end']}")
    lines.append(f"**Symbols:** {', '.join(run_meta['symbols'])}")
    lines.append(f"**Data source:** {run_meta['data_dir']}")
    lines.append(f"**Methodology:** ADR 003 / `.context/06_decisions/003_retest_geometry_study_corrected_methodology.md`")
    lines.append("")
    lines.append("**Corrected retest timing:** walk begins only from the first M15 candle whose "
                 "open is >= the CLOSE time of the BOS-confirming H1 candle. This supersedes the "
                 "v1 study which walked from OB formation time (creating the look-ahead bias A3 "
                 "identified).")
    lines.append("")
    lines.append("**Twin geometry:** every retest is classified under TWO outcome specs:")
    lines.append("")
    lines.append("- **Geometry A** — wider SL (0.5 x H1 ATR beyond OB), 1 OB-body target, 12h window")
    lines.append("- **Geometry B (Test A)** — tighter SL (0.1%/$0.00015 beyond OB), 1.5R target, 3h window")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(_geometry_report_block(records, geometry="a"))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(_geometry_report_block(records, geometry="b"))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Geometry A vs Geometry B — reconciliation")
    lines.append("")
    ob_a = outcome_breakdown(records, geometry="a")
    ob_b = outcome_breakdown(records, geometry="b")
    _, _, rate_a = continuation_rate(records, geometry="a")
    _, _, rate_b = continuation_rate(records, geometry="b")

    lines.append(f"- Geometry A ex-UNR continuation rate (combined): **{rate_a:.1f}%** "
                 f"(CONTINUED={ob_a['CONTINUED']}, REVERSED={ob_a['REVERSED']}, "
                 f"UNRESOLVED={ob_a['UNRESOLVED']})")
    lines.append(f"- Geometry B ex-UNR continuation rate (combined): **{rate_b:.1f}%** "
                 f"(CONTINUED={ob_b['CONTINUED']}, REVERSED={ob_b['REVERSED']}, "
                 f"UNRESOLVED={ob_b['UNRESOLVED']})")
    lines.append("")
    lines.append(
        "The two geometries measure different questions on the SAME retest:"
    )
    lines.append(
        "- Geometry A asks 'does price continue one OB-body-length within 12h without "
        "wiping past the OB + 0.5 ATR buffer?'. The wider SL plus longer horizon make "
        "both CONTINUED and UNRESOLVED more likely than under Geometry B, while absolute "
        "REVERSED count is typically lower."
    )
    lines.append(
        "- Geometry B asks 'does price hit a 1.5R target within 3h without hitting the "
        "tight Test A SL?'. Tight SL + short horizon produce more REVERSED and fewer "
        "UNRESOLVED. This number is the one directly comparable to Test A's ~70% "
        "baseline (n=219, +17pp, p=0.003)."
    )
    lines.append("")
    lines.append(
        "**Validation test:** if Geometry B's combined continuation rate is close to "
        "~65-75%, the corrected timing is consistent with Test A's independent finding. "
        "A large gap in either direction indicates a methodology issue that deserves "
        "investigation beyond what this study can answer."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Notes:")
    lines.append("- UNRESOLVED retests are EXCLUDED from ex-UNR continuation-rate tables.")
    lines.append("- 95% CI is Wilson score.")
    lines.append("- Tercile cut-points are per-bucket relative percentiles.")
    lines.append(f"- Retest timing invariant enforced at classify-time: "
                 f"retest_ts > bos_confirm_ts (strict).")
    lines.append("- Geometry B SL rule is taken verbatim from Test A "
                 "(`scripts/ob_retest_comprehensive.py`). The `0.00015` absolute "
                 "buffer is microscopic for JPY pairs and US30; this is faithful "
                 "reproduction of Test A, not a recommended production SL.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Live-period join
# ---------------------------------------------------------------------------


def _load_live_evaluations_for_symbol(
    symbol: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Load live_evaluations JSONL for [start_date, end_date]."""
    d = start_date
    rows: list[dict] = []
    sym_dir = LIVE_EVALUATIONS_DIR / symbol
    if not sym_dir.exists():
        return rows
    while d <= end_date:
        fpath = sym_dir / f"{d.isoformat()}.jsonl"
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rows.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to read %s: %s", fpath, exc)
        d += timedelta(days=1)
    return rows


def _normalize_to_m15(dt: datetime) -> datetime:
    """Round a datetime down to the containing M15 candle open time."""
    minute = (dt.minute // 15) * 15
    return dt.replace(minute=minute, second=0, microsecond=0)


def _m15_candle_open_from_time_str(t: str) -> datetime:
    if t.endswith("Z"):
        dt = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    else:
        try:
            dt = datetime.fromisoformat(t)
        except ValueError:
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return _normalize_to_m15(dt)


def join_live_evaluations(
    retests: list[RetestRecord],
    start_date: date,
    end_date: date,
    geometry: str = "b",
) -> dict[str, Any]:
    """Join retests with live_evaluations rows. Uses Geometry B outcome
    by default (live-relevant). Set ``geometry='a'`` for the theoretical
    baseline.

    Returns aggregate metrics per ADR 003 Step 8 (emphasis on Geom B):
      - coverage_by_symbol: {symbol: (matched, total)}
      - candidate_matches: # CANDIDATEs with a matching retest
      - candidates_without_retest: # CANDIDATEs with no matching retest
      - misses: # retests that CONTINUED but got NO_TRADE or were not evaluated
      - misses_by_reason: {reason_str: count}
      - false_positives: # CANDIDATEs that matched a REVERSED retest
      - retest_match_rows: per-retest rows for diagnostic inspection
      - geometry: the geometry used for outcome attribution
    """
    outcome_attr = "outcome_a" if geometry == "a" else "outcome_b"

    retests_by_key: dict[tuple[str, str], RetestRecord] = {}
    for r in retests:
        try:
            rt_bucket = _m15_candle_open_from_time_str(r.retest_ts)
        except ValueError:
            continue
        retests_by_key[(r.symbol, rt_bucket.isoformat())] = r

    coverage_by_symbol: dict[str, tuple[int, int]] = {}
    candidate_matches = 0
    candidates_without_retest = 0
    misses = 0
    misses_by_reason: dict[str, int] = {}
    false_positives = 0
    retest_match_rows: list[dict[str, Any]] = []

    live_index: dict[tuple[str, str], list[dict]] = {}
    all_symbols_in_retests = sorted({r.symbol for r in retests})
    for sym in all_symbols_in_retests:
        live_rows = _load_live_evaluations_for_symbol(sym, start_date, end_date)
        for row in live_rows:
            candle_ts = row.get("candle_time") or row.get("timestamp")
            if not candle_ts:
                continue
            try:
                bucket = _m15_candle_open_from_time_str(candle_ts)
            except ValueError:
                continue
            live_index.setdefault((sym, bucket.isoformat()), []).append(row)

    by_sym_match: dict[str, list[int]] = {}
    for r in retests:
        by_sym_match.setdefault(r.symbol, [0, 0])
        try:
            rt_bucket = _m15_candle_open_from_time_str(r.retest_ts)
        except ValueError:
            continue
        live_rows = live_index.get((r.symbol, rt_bucket.isoformat()), [])
        by_sym_match[r.symbol][1] += 1
        r_outcome = getattr(r, outcome_attr)
        if live_rows:
            by_sym_match[r.symbol][0] += 1
            lr = live_rows[0]
            match_row = {
                "symbol": r.symbol,
                "retest_ts": r.retest_ts,
                "bos_confirm_ts": r.bos_confirm_ts,
                "side": r.side,
                "outcome_a": r.outcome_a,
                "outcome_b": r.outcome_b,
                "live_decision": lr.get("decision"),
                "live_kill_zone": lr.get("kill_zone"),
                "no_trade_reason": lr.get("no_trade_reason"),
                "setup_grade": lr.get("setup_grade"),
                "framework": lr.get("framework"),
            }
            retest_match_rows.append(match_row)

            if r_outcome == "CONTINUED" and lr.get("decision") != "CANDIDATE":
                misses += 1
                reason = lr.get("no_trade_reason") or "(no reason)"
                key = reason[:120]
                misses_by_reason[key] = misses_by_reason.get(key, 0) + 1
        else:
            if r_outcome == "CONTINUED":
                misses += 1
                misses_by_reason["(no live evaluation at this candle)"] = (
                    misses_by_reason.get("(no live evaluation at this candle)", 0) + 1
                )

    for sym, (m, n) in by_sym_match.items():
        coverage_by_symbol[sym] = (m, n)

    for (sym, bucket), rows in live_index.items():
        for row in rows:
            if row.get("decision") != "CANDIDATE":
                continue
            r = retests_by_key.get((sym, bucket))
            if r is None:
                candidates_without_retest += 1
            else:
                candidate_matches += 1
                if getattr(r, outcome_attr) == "REVERSED":
                    false_positives += 1

    return {
        "coverage_by_symbol": coverage_by_symbol,
        "candidate_matches": candidate_matches,
        "candidates_without_retest": candidates_without_retest,
        "misses": misses,
        "misses_by_reason": misses_by_reason,
        "false_positives": false_positives,
        "retest_match_rows": retest_match_rows,
        "geometry": geometry,
    }


def build_live_period_report_md(
    records: list[RetestRecord],
    join_b: dict[str, Any],
    join_a: dict[str, Any],
    run_meta: dict,
) -> str:
    """Build the live-period markdown report (emphasis Geom B, ref Geom A)."""
    lines: list[str] = []
    lines.append("# Retest Geometry Study (v2, ADR 003) — Live-Period Report")
    lines.append("")
    lines.append(f"**Generated:** {run_meta['generated']}")
    lines.append(f"**Window:** {LIVE_PERIOD_START} -> {run_meta['end']}")
    lines.append(f"**Symbols:** {', '.join(run_meta['symbols'])}")
    lines.append(f"**Methodology:** ADR 003 live-period section.")
    lines.append("")
    lines.append("This report emphasizes **Geometry B** (Test A calibration) because it "
                 "is directly comparable to live execution semantics (1.5R target, tight "
                 "SL). Geometry A numbers are included alongside for reference.")
    lines.append("")
    lines.append("## Coverage — retests with a matching live evaluation")
    lines.append("")
    lines.append("A retest is 'covered' if a live_evaluations JSONL row exists at the")
    lines.append("same M15 candle bucket. Non-covered retests are expected outside kill")
    lines.append("zones (live system isn't running) and during orchestrator downtime.")
    lines.append("")
    lines.append("| symbol | matched | total | coverage |")
    lines.append("|---|---|---|---|")
    for sym in sorted(join_b["coverage_by_symbol"].keys()):
        m, n = join_b["coverage_by_symbol"][sym]
        pct = m / n * 100.0 if n else 0.0
        lines.append(f"| {sym} | {m} | {n} | {pct:.1f}% |")
    lines.append("")
    lines.append("## Alignment — CANDIDATEs vs mechanically-detected retests")
    lines.append("")
    cm_b = join_b["candidate_matches"]
    cwor_b = join_b["candidates_without_retest"]
    cm_a = join_a["candidate_matches"]
    cwor_a = join_a["candidates_without_retest"]
    lines.append(f"- CANDIDATEs issued at an M15 bucket that matches a mechanical retest: "
                 f"**{cm_b}** (Geom B) / **{cm_a}** (Geom A — same by definition, "
                 f"geometry only affects outcome classification, not bucket join)")
    lines.append(f"- CANDIDATEs issued WITHOUT a matching mechanical retest: "
                 f"**{cwor_b}**")
    lines.append("")
    lines.append("## Mechanical outcomes (side-by-side)")
    lines.append("")
    lines.append("Of the CANDIDATEs that matched a mechanical retest, what did our")
    lines.append("walk-forward classification say — under each geometry?")
    lines.append("")
    match_rows = join_b["retest_match_rows"]  # same rows for both geometries
    counts_a = {"CONTINUED": 0, "REVERSED": 0, "UNRESOLVED": 0}
    counts_b = {"CONTINUED": 0, "REVERSED": 0, "UNRESOLVED": 0}
    for mr in match_rows:
        if mr.get("live_decision") == "CANDIDATE":
            counts_a[mr["outcome_a"]] = counts_a.get(mr["outcome_a"], 0) + 1
            counts_b[mr["outcome_b"]] = counts_b.get(mr["outcome_b"], 0) + 1
    lines.append("| mechanical outcome | Geometry A | Geometry B |")
    lines.append("|---|---|---|")
    for o in ("CONTINUED", "REVERSED", "UNRESOLVED"):
        lines.append(f"| {o} | {counts_a.get(o, 0)} | {counts_b.get(o, 0)} |")
    lines.append("")
    lines.append("## Misses — Geometry B (live-relevant)")
    lines.append("")
    lines.append("Retests that CONTINUED per Geometry B mechanical classification but the")
    lines.append("live system did NOT issue a CANDIDATE (either NO_TRADE or no evaluation).")
    lines.append("")
    lines.append(f"**Total misses (Geom B):** {join_b['misses']}")
    lines.append(f"**Total misses (Geom A, reference):** {join_a['misses']}")
    lines.append("")
    lines.append("**Miss reasons — Geometry B (no_trade_reason prefix -> count):**")
    lines.append("")
    if join_b["misses_by_reason"]:
        lines.append("| reason | n |")
        lines.append("|---|---|")
        for reason, n in sorted(
            join_b["misses_by_reason"].items(), key=lambda x: -x[1]
        ):
            reason_safe = reason.replace("|", "\\|")
            lines.append(f"| {reason_safe} | {n} |")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## False positives — Geometry B (live-relevant)")
    lines.append("")
    lines.append("CANDIDATEs issued where the Geometry B mechanical classification says REVERSED.")
    lines.append("")
    lines.append(f"**Total false positives (Geom B):** {join_b['false_positives']}")
    lines.append(f"**Total false positives (Geom A, reference):** {join_a['false_positives']}")
    lines.append("")
    lines.append("## Per-retest diagnostic rows (first 30)")
    lines.append("")
    lines.append("| symbol | retest_ts | bos_confirm_ts | side | outcome_A | outcome_B | live decision | KZ | setup grade |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for mr in match_rows[:30]:
        lines.append(
            f"| {mr['symbol']} | {mr['retest_ts']} | {mr['bos_confirm_ts']} | "
            f"{mr['side']} | {mr['outcome_a']} | {mr['outcome_b']} | "
            f"{mr.get('live_decision', '')} | "
            f"{mr.get('live_kill_zone') or ''} | {mr.get('setup_grade') or ''} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Notes:")
    lines.append(f"- Live-period window: {LIVE_PERIOD_START} onwards.")
    lines.append("- Bucket-matching: retest_ts rounded down to M15 boundary, compared to live eval candle_time.")
    lines.append("- A retest outside kill-zone hours has no live eval by design — those show as 'no live evaluation'.")
    lines.append("- **Primary geometry for live-period interpretation: B.** A is reported alongside for completeness.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_study(
    symbols: list[str],
    start_date: date,
    end_date: date,
    data_dir: Path,
    out_dir: Path,
    report: str = "both",
) -> int:
    """Main entrypoint. Writes per-symbol + combined CSVs, plus md reports.

    Twin geometry: classification under Geom A and Geom B is computed on the
    same retest candles in a single pass.
    """
    if _IMPORT_ERROR is not None:
        logger.error("Production imports failed: %s", _IMPORT_ERROR)
        return 2

    hist_dir = out_dir / "historical"
    live_dir = out_dir / "live_period"
    hist_dir.mkdir(parents=True, exist_ok=True)
    live_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[RetestRecord] = []
    run_meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "symbols": symbols,
        "data_dir": str(data_dir),
    }

    for sym in symbols:
        logger.info("Processing %s...", sym)
        recs = build_retests_for_symbol(sym, start_date, end_date, data_dir)
        if recs:
            write_retest_csv(recs, hist_dir / f"{sym}_retests.csv")
            logger.info("%s: wrote %d retests", sym, len(recs))
        else:
            logger.warning("%s: 0 retests - writing header-only CSV", sym)
            write_retest_csv([], hist_dir / f"{sym}_retests.csv")
        all_records.extend(recs)

    all_records.sort(key=lambda r: (r.symbol, r.retest_ts))
    write_retest_csv(all_records, hist_dir / "combined_retests.csv")
    logger.info("Combined: %d retests total", len(all_records))

    if report in ("historical", "both"):
        md = build_historical_report_md(all_records, run_meta)
        with open(hist_dir / "geometry_report.md", "w", encoding="utf-8") as fh:
            fh.write(md)
        logger.info("Wrote %s", hist_dir / "geometry_report.md")

    if report in ("live", "both"):
        live_records = [r for r in all_records
                        if _utc_date(r.retest_ts) >= LIVE_PERIOD_START]
        by_sym_live: dict[str, list[RetestRecord]] = {}
        for r in live_records:
            by_sym_live.setdefault(r.symbol, []).append(r)
        for sym in symbols:
            write_retest_csv(by_sym_live.get(sym, []), live_dir / f"{sym}_retests.csv")
        write_retest_csv(live_records, live_dir / "combined_retests.csv")
        logger.info("Live-period CSVs: %d retests total", len(live_records))

        # Run the join under both geometries; report emphasizes B.
        join_b = join_live_evaluations(live_records, LIVE_PERIOD_START, end_date, geometry="b")
        join_a = join_live_evaluations(live_records, LIVE_PERIOD_START, end_date, geometry="a")
        md = build_live_period_report_md(live_records, join_b, join_a, run_meta)
        with open(live_dir / "geometry_report.md", "w", encoding="utf-8") as fh:
            fh.write(md)
        logger.info("Wrote %s", live_dir / "geometry_report.md")

    return 0


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else None)
    p.add_argument("--symbols", type=str, default=None,
                   help="Comma-separated symbols (default: all 5).")
    p.add_argument("--start", type=str, default="2026-01-01",
                   help="Start date YYYY-MM-DD (default 2026-01-01).")
    p.add_argument("--end", type=str, default="2026-04-17",
                   help="End date YYYY-MM-DD (default 2026-04-17).")
    p.add_argument("--data-dir", type=str, default=None,
                   help="Historical data dir (default data/historical).")
    p.add_argument("--out-dir", type=str, default=None,
                   help="Output directory (default research/retest_geometry/outputs).")
    p.add_argument("--report", type=str, choices=("historical", "live", "both"),
                   default="both",
                   help="Which report to generate (default both).")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    global DATA_DIR, OUT_DIR
    if args.data_dir:
        DATA_DIR = Path(args.data_dir).resolve()
    if args.out_dir:
        OUT_DIR = Path(args.out_dir).resolve()

    symbols = SYMBOLS if args.symbols is None else [
        s.strip() for s in args.symbols.split(",") if s.strip()
    ]
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    return run_study(symbols, start, end, DATA_DIR, OUT_DIR, report=args.report)


if __name__ == "__main__":
    sys.exit(main())
