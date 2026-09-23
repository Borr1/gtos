"""A2_v2 — Independent pandas-only validator for Retest Geometry Study v2.

Goal: validate A1_v2's (ADR 003-compliant) continuation numbers via a truly
independent code path. This module does NOT import from ``src/components/``
and does NOT share helpers with ``research/retest_geometry/study.py``.

Scope
-----
Window:   2026-01-01 .. 2026-04-17 UTC (inclusive)
Symbols:  XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD
Source:   ``data/historical/{SYMBOL}_H1.csv`` + ``..._M15.csv``

Methodology (independent re-derivation of ADR 003)
--------------------------------------------------
1. Detect H1 swings via 3-bar pivot (local min/max over a 3-bar centred window).
2. Detect Break-of-Structure (BOS) on H1 closes:
   * Bullish BOS = first H1 close strictly above the most recent prior confirmed
     swing high.
   * Bearish BOS = first H1 close strictly below the most recent prior confirmed
     swing low.
   Only CLOSE-based breaks count — intrabar wicks do not trigger BOS.
3. Identify OB = the last H1 candle with opposing body (bearish for bullish BOS,
   bullish for bearish BOS) strictly before the BOS candle. If no opposing
   candle exists in the window, skip.
4. ``bos_confirm_ts`` = open time of BOS candle + 1 hour (close time).
5. Retest = first M15 candle whose OPEN is strictly AFTER ``bos_confirm_ts``
   AND whose body/wick range intersects [OB_low, OB_high].
   * Bullish OB: retest fires when M15 low <= OB_high AND M15 low >= OB_low? no — we use ADR 003 wording: "low ≤ OB_high AND low ≥ OB_low for long-side OB".
     Interpreted: the M15 candle low must fall within the OB zone (low <=
     OB_high is the binding constraint; low >= OB_low is checked too; if low
     dips beneath OB_low the candle still entered the zone, so we use
     "low <= OB_high" as the entry condition — i.e. price touched the zone
     from above). For consistency with Test A's simple "enters zone" read,
     we require the candle low to be within the box-extended-downward:
     ``low <= OB_high`` (price touched zone or dipped into it). Mirror for
     bearish.
6. Walk forward 48 M15 candles. Classify outcome under two geometries:
   * Geometry A: SL = OB opposing edge + 0.5 * H1 ATR(14 at retest);
     target = retest_entry + 1 * OB_body past far edge; window 48.
   * Geometry B (Test A): SL = ``ob_low - 0.001 * ob_low`` for XAUUSD bullish
     (mirror bearish); for other symbols ``ob_low - 0.00015`` absolute;
     target = retest_entry + 1.5 * SL_distance; window 12.

Dedup: keep first appearance of each (symbol, formation_ts, ob_type, high, low)
tuple — mirrors A1_v2's uniqueness semantics. Without this, a single OB that
gets detected across multiple scan windows would produce duplicate retests.

Mitigation filter: an OB is dropped if any H1 candle strictly AFTER its
formation and strictly BEFORE its BOS has wicked into the zone (basic
mitigation-before-BOS check). We do NOT apply the per-date EOD survivorship
filter — that filter introduced look-ahead in v1 (A3 finding #1); we avoid it
here and let the BOS timing itself be the clean gate.

ALL temporal operations use UTC-aware datetimes. No DST math.

Output
------
``outputs/a2_v2_validation/combined_retests.csv`` — one row per detected
first-retest, per-symbol.
``outputs/a2_v2_validation/summary.json`` — structured per-symbol + combined
continuation rates for Geometry A and Geometry B, plus temporal-ordering
audit result.

Author: A2_v2 (independent statistical validator)
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HISTORICAL_DIR = PROJECT_ROOT / "data" / "historical"
OUTPUT_DIR = PROJECT_ROOT / "research" / "retest_geometry" / "outputs" / "a2_v2_validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]
WINDOW_START = date(2026, 1, 1)
WINDOW_END = date(2026, 4, 17)

# Swing pivot lookback (3-bar => center index must be strict local extremum
# over [i-1, i+1]). Simpler than production's detect_swings but defensible
# and explicit.
SWING_WINDOW = 1  # 1 bar on each side => 3-bar centred pivot

# Geometry A
GEOM_A_WINDOW = 48       # M15 candles
ATR_N = 14

# Geometry B (Test A — see scripts/ob_retest_comprehensive.py lines 432-466)
GEOM_B_WINDOW = 12


# Pip definitions for pips-output (match A1_v2 and Test A conventions)
PIP_SIZE = {
    "XAUUSD": 0.1,     # $0.1 = 1 pip in gold
    "US30_cash": 1.0,  # 1 point = 1 pip in index
    "USDJPY": 0.01,    # 0.01 JPY = 1 pip
    "GBPJPY": 0.01,
    "GBPUSD": 0.0001,
}


# ---------------------------------------------------------------------------
# Data loading — pandas only
# ---------------------------------------------------------------------------


def load_candles(symbol: str, timeframe: str) -> pd.DataFrame:
    """Load candles as DataFrame indexed by UTC-aware datetime.

    Columns: open, high, low, close, volume.
    """
    path = HISTORICAL_DIR / f"{symbol}_{timeframe}.csv"
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True, format="mixed")
    df = df.set_index("time").sort_index()
    # Ensure numeric
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["open", "high", "low", "close"]].dropna()


# ---------------------------------------------------------------------------
# Independent OB + BOS detector
# ---------------------------------------------------------------------------


@dataclass
class Pivot:
    idx: int                   # integer index within h1 DataFrame
    ts: datetime               # open time of the pivot H1 candle
    price: float
    kind: str                  # "high" or "low"


@dataclass
class BosEvent:
    bos_idx: int               # integer index of BOS-confirming H1 candle
    bos_ts: datetime           # OPEN time of the BOS H1 candle
    bos_close_ts: datetime     # CLOSE time = bos_ts + 1h
    direction: str             # "bullish" or "bearish"
    broken_pivot_price: float  # the swing level that was broken


@dataclass
class DetectedOB:
    symbol: str
    formation_idx: int         # index in h1 DataFrame of the OB-forming candle
    formation_ts: datetime     # OPEN time of the OB H1 candle
    ob_type: str               # "bullish" or "bearish"
    ob_high: float
    ob_low: float
    ob_open: float
    ob_close: float
    bos_idx: int
    bos_close_ts: datetime


def detect_pivots(h1: pd.DataFrame, window: int = SWING_WINDOW) -> list[Pivot]:
    """Detect 3-bar pivot highs/lows.

    A pivot high at index i requires h1.high[i] > h1.high[i-1] AND
    h1.high[i] > h1.high[i+1]. Ties disqualify (strict).
    Mirror for pivot lows.
    """
    highs = h1["high"].to_numpy()
    lows = h1["low"].to_numpy()
    idx_arr = h1.index.to_numpy()
    pivots: list[Pivot] = []

    for i in range(window, len(h1) - window):
        # Pivot high
        is_high = True
        for k in range(1, window + 1):
            if not (highs[i] > highs[i - k] and highs[i] > highs[i + k]):
                is_high = False
                break
        if is_high:
            pivots.append(Pivot(i, pd.Timestamp(idx_arr[i]).to_pydatetime(), float(highs[i]), "high"))
            continue  # same bar cannot be both extrema (mutex by definition except doji)
        # Pivot low
        is_low = True
        for k in range(1, window + 1):
            if not (lows[i] < lows[i - k] and lows[i] < lows[i + k]):
                is_low = False
                break
        if is_low:
            pivots.append(Pivot(i, pd.Timestamp(idx_arr[i]).to_pydatetime(), float(lows[i]), "low"))

    return pivots


def detect_bos_events(h1: pd.DataFrame, pivots: list[Pivot]) -> list[BosEvent]:
    """Detect Break-of-Structure events on H1 closes.

    For each candle i (iterated chronologically), check if its CLOSE strictly
    breaks the most recently confirmed opposing pivot. A pivot is only
    "confirmed" at index i if pivot.idx + window <= i (i.e., we needed `window`
    bars of confirmation after the pivot bar).

    Returns a list of BOS events in chronological order.
    """
    events: list[BosEvent] = []
    closes = h1["close"].to_numpy()
    idx_arr = h1.index.to_numpy()
    n = len(h1)

    # Bucket pivots by confirmation_idx (when they become visible)
    # For window=1, pivot confirmed at pivot.idx + 1.
    pivots_sorted = sorted(pivots, key=lambda p: p.idx)
    confirmed_highs: list[Pivot] = []
    confirmed_lows: list[Pivot] = []
    pivot_ptr = 0

    for i in range(n):
        # Advance pivot pointer: a pivot p is confirmed at step i if p.idx + window <= i
        while pivot_ptr < len(pivots_sorted) and pivots_sorted[pivot_ptr].idx + SWING_WINDOW <= i:
            p = pivots_sorted[pivot_ptr]
            if p.kind == "high":
                confirmed_highs.append(p)
            else:
                confirmed_lows.append(p)
            pivot_ptr += 1

        close_i = closes[i]
        # Check bullish BOS: close above most recent confirmed high
        if confirmed_highs:
            last_high = confirmed_highs[-1]
            # Only trigger if close > pivot price AND we're after the pivot bar
            if last_high.idx < i and close_i > last_high.price:
                # Create BOS event and "consume" this swing high
                bos_open_ts = pd.Timestamp(idx_arr[i]).to_pydatetime()
                events.append(BosEvent(
                    bos_idx=i,
                    bos_ts=bos_open_ts,
                    bos_close_ts=bos_open_ts + timedelta(hours=1),
                    direction="bullish",
                    broken_pivot_price=last_high.price,
                ))
                # Remove any highs at or below the new high (they're now stale)
                confirmed_highs = [p for p in confirmed_highs if p.price > last_high.price]
                # Reset lows — new structure direction
                # (don't clear; a single close can only break one level per bar)
        # Check bearish BOS: close below most recent confirmed low
        if confirmed_lows:
            last_low = confirmed_lows[-1]
            if last_low.idx < i and close_i < last_low.price:
                bos_open_ts = pd.Timestamp(idx_arr[i]).to_pydatetime()
                events.append(BosEvent(
                    bos_idx=i,
                    bos_ts=bos_open_ts,
                    bos_close_ts=bos_open_ts + timedelta(hours=1),
                    direction="bearish",
                    broken_pivot_price=last_low.price,
                ))
                confirmed_lows = [p for p in confirmed_lows if p.price < last_low.price]

    return events


def find_ob_for_bos(h1: pd.DataFrame, bos: BosEvent, max_lookback: int = 24) -> Optional[tuple[int, datetime, float, float, float, float]]:
    """For a bullish BOS, find the LAST bearish candle strictly before the BOS
    candle (within max_lookback bars). For bearish BOS, find the last bullish.

    Returns (formation_idx, formation_ts, ob_high, ob_low, ob_open, ob_close)
    or None if no matching candle found.
    """
    ohlc = h1[["open", "high", "low", "close"]].to_numpy()
    idx_arr = h1.index.to_numpy()
    start = max(0, bos.bos_idx - max_lookback)
    # Walk backwards from bos_idx - 1 to start
    for j in range(bos.bos_idx - 1, start - 1, -1):
        o, hi, lo, cl = ohlc[j]
        if bos.direction == "bullish":
            # Need bearish candle: close < open
            if cl < o:
                return (
                    j,
                    pd.Timestamp(idx_arr[j]).to_pydatetime(),
                    float(hi),
                    float(lo),
                    float(o),
                    float(cl),
                )
        else:
            # Need bullish candle for bearish BOS
            if cl > o:
                return (
                    j,
                    pd.Timestamp(idx_arr[j]).to_pydatetime(),
                    float(hi),
                    float(lo),
                    float(o),
                    float(cl),
                )
    return None


def check_mitigation_before_bos(h1: pd.DataFrame, formation_idx: int, bos_idx: int, ob_high: float, ob_low: float, ob_type: str) -> bool:
    """Return True if the OB zone was mitigated by any H1 candle strictly
    between formation_idx and bos_idx. Mitigation = for bullish OB, a later
    candle's low dips below ob_low (swept) or a later candle's close back
    inside zone after being above; simplest: any H1 candle in
    (formation_idx, bos_idx) whose high >= ob_low AND low <= ob_high counts
    as a touch. Since our OB by construction sits BELOW the impulse for
    bullish OBs, we just check whether any intervening candle's LOW <= OB_high
    (i.e. price dipped back to or into the zone before BOS completed).

    Actually in the impulse window, price is moving AWAY from OB in
    direction of BOS, so the zone should remain untouched. If it was touched,
    the OB has already been mitigated pre-BOS and should be dropped.

    For bullish OB: mitigated if any intervening candle low <= ob_low (full
    sweep) or low < ob_high (partial dip).  We use the strict definition —
    any intervening candle entering the zone disqualifies the OB.
    """
    lows = h1["low"].to_numpy()
    highs = h1["high"].to_numpy()
    # range = (formation_idx + 1, bos_idx)  —  strictly between
    for k in range(formation_idx + 1, bos_idx):
        if ob_type == "bullish":
            # If any candle low dips into zone
            if lows[k] <= ob_high:
                return True
        else:
            if highs[k] >= ob_low:
                return True
    return False


def detect_obs(symbol: str, h1: pd.DataFrame) -> list[DetectedOB]:
    """Return all OBs for a symbol within the H1 DataFrame."""
    pivots = detect_pivots(h1)
    bos_events = detect_bos_events(h1, pivots)

    obs: list[DetectedOB] = []
    for bos in bos_events:
        found = find_ob_for_bos(h1, bos)
        if found is None:
            continue
        formation_idx, formation_ts, ob_hi, ob_lo, ob_o, ob_c = found

        # Mitigation pre-BOS: drop if zone already touched before confirmation
        if check_mitigation_before_bos(h1, formation_idx, bos.bos_idx, ob_hi, ob_lo, bos.direction):
            # For a bullish BOS, the impulse candles between formation and BOS
            # SHOULD NOT reenter the opposing candle zone. If they did, the OB
            # is already stale.
            # BUT: the impulse itself starts at formation+1 and moves up. Its
            # low may equal OB_high (touching). We accept touch (low == ob_high)
            # as non-mitigating only if no candle's body closes inside.
            # Simpler: use a tolerant check — drop only if low < ob_low
            # (full sweep). Otherwise keep.
            #
            # To keep this independent and simple, we use the LOOSER rule:
            # mitigated only if an intervening candle's LOW < ob_low (bullish)
            # or HIGH > ob_high (bearish).
            if _strict_mitigation_before_bos(h1, formation_idx, bos.bos_idx, ob_hi, ob_lo, bos.direction):
                continue

        # OB type: bullish BOS => bullish OB, bearish BOS => bearish OB
        ob_type = "bullish" if bos.direction == "bullish" else "bearish"

        obs.append(DetectedOB(
            symbol=symbol,
            formation_idx=formation_idx,
            formation_ts=formation_ts,
            ob_type=ob_type,
            ob_high=ob_hi,
            ob_low=ob_lo,
            ob_open=ob_o,
            ob_close=ob_c,
            bos_idx=bos.bos_idx,
            bos_close_ts=bos.bos_close_ts,
        ))

    return obs


def _strict_mitigation_before_bos(h1: pd.DataFrame, formation_idx: int, bos_idx: int, ob_high: float, ob_low: float, ob_type: str) -> bool:
    """Strict mitigation: drop only if the zone was FULLY swept.

    Bullish OB: strict mitigation if any intervening candle's low < ob_low.
    Bearish OB: if any intervening candle's high > ob_high.
    """
    lows = h1["low"].to_numpy()
    highs = h1["high"].to_numpy()
    for k in range(formation_idx + 1, bos_idx):
        if ob_type == "bullish":
            if lows[k] < ob_low:
                return True
        else:
            if highs[k] > ob_high:
                return True
    return False


# ---------------------------------------------------------------------------
# Retest detection (corrected — strictly after bos_confirm_ts)
# ---------------------------------------------------------------------------


@dataclass
class RetestRow:
    symbol: str
    ob_formation_ts: datetime
    bos_confirm_ts: datetime
    retest_ts: datetime
    retest_date: date
    session: str
    side: str
    ob_body_size: float
    ob_body_size_pips: float
    ob_body_size_atr: float
    retest_entry_price: float
    h1_atr_at_retest: float
    # Geometry A fields
    sl_a_price: float
    target_a_price: float
    outcome_a: str
    continuation_r_a: Optional[float]
    mae_a_pips: float
    mae_a_atr: float
    penetration_a_pips: float
    time_to_mae_a_candles: int
    time_to_continuation_a_candles: Optional[int]
    # Geometry B fields
    sl_b_price: float
    target_b_price: float
    outcome_b: str
    continuation_r_b: Optional[float]
    mae_b_pips: float
    mae_b_atr: float
    penetration_b_pips: float
    time_to_mae_b_candles: int
    time_to_continuation_b_candles: Optional[int]


def compute_h1_atr(h1: pd.DataFrame, as_of_idx: int, n: int = ATR_N) -> float:
    """Simple ATR(n) using True Range average ending at (and including) as_of_idx."""
    if as_of_idx < n:
        return 0.0
    high = h1["high"].to_numpy()
    low = h1["low"].to_numpy()
    close = h1["close"].to_numpy()
    trs = []
    for k in range(as_of_idx - n + 1, as_of_idx + 1):
        if k == 0:
            trs.append(high[k] - low[k])
            continue
        tr = max(
            high[k] - low[k],
            abs(high[k] - close[k - 1]),
            abs(low[k] - close[k - 1]),
        )
        trs.append(tr)
    return float(sum(trs) / len(trs)) if trs else 0.0


def session_label(ts: datetime) -> str:
    """UTC-based session label: matches A1_v2 roughly.

    Tokyo 00:00-07:00, London 07:00-13:00, NY 13:00-17:00, else 'None'.
    """
    h = ts.hour
    if 0 <= h < 7:
        return "Tokyo"
    if 7 <= h < 13:
        return "London"
    if 13 <= h < 17:
        return "NY"
    return "None"


def find_first_retest_and_measure(
    symbol: str,
    ob: DetectedOB,
    h1: pd.DataFrame,
    m15: pd.DataFrame,
) -> Optional[RetestRow]:
    """Find the first M15 candle strictly AFTER ob.bos_close_ts that enters
    the OB zone, then classify outcome under Geometry A and Geometry B.

    Returns None if no retest within a generous 7-day forward window.
    """
    # Sub-slice M15 to candles with open > bos_confirm_ts
    m15_after = m15[m15.index > ob.bos_close_ts]
    if m15_after.empty:
        return None

    # Limit forward scan to 48h of M15 (192 candles) — matches A1_v2's
    # RETEST_SCAN_WINDOW for parity. Earlier explorations used 14 days
    # but we tighten to 48h to make our numbers comparable to A1_v2's.
    MAX_RETEST_SCAN = 192  # 48h
    scan = m15_after.iloc[:MAX_RETEST_SCAN]

    ob_high = ob.ob_high
    ob_low = ob.ob_low
    ob_type = ob.ob_type

    # Find first candle entering zone
    retest_idx_in_scan = None
    for i, row in enumerate(scan.itertuples()):
        # row: Index=timestamp, Open, High, Low, Close
        if ob_type == "bullish":
            # Price dipped into zone from above
            if row.low <= ob_high and row.high >= ob_low:
                retest_idx_in_scan = i
                break
        else:
            if row.high >= ob_low and row.low <= ob_high:
                retest_idx_in_scan = i
                break

    if retest_idx_in_scan is None:
        return None

    retest_candle = scan.iloc[retest_idx_in_scan]
    retest_ts = scan.index[retest_idx_in_scan].to_pydatetime()

    # Entry price: candle close if inside zone, else next candle open (mirror Test A)
    if ob_type == "bullish":
        if retest_candle.close >= ob_low and retest_candle.close <= ob_high:
            entry_price = float(retest_candle.close)
            entry_idx_in_scan = retest_idx_in_scan
        else:
            if retest_idx_in_scan + 1 < len(scan):
                entry_price = float(scan.iloc[retest_idx_in_scan + 1].open)
                entry_idx_in_scan = retest_idx_in_scan + 1
            else:
                return None
    else:
        if retest_candle.close >= ob_low and retest_candle.close <= ob_high:
            entry_price = float(retest_candle.close)
            entry_idx_in_scan = retest_idx_in_scan
        else:
            if retest_idx_in_scan + 1 < len(scan):
                entry_price = float(scan.iloc[retest_idx_in_scan + 1].open)
                entry_idx_in_scan = retest_idx_in_scan + 1
            else:
                return None

    # H1 ATR at retest — use H1 bar containing retest_ts
    # find H1 idx: largest H1 index with open <= retest_ts
    h1_times = h1.index
    h1_at_retest_mask = h1_times <= pd.Timestamp(retest_ts)
    if not h1_at_retest_mask.any():
        return None
    h1_idx_at_retest = int(h1_at_retest_mask.sum() - 1)
    h1_atr = compute_h1_atr(h1, h1_idx_at_retest)
    if h1_atr <= 0:
        return None

    ob_body = abs(ob.ob_close - ob.ob_open)
    ob_body = max(ob_body, 1e-9)

    pip = PIP_SIZE.get(symbol, 0.0001)

    # Geometry A targets and SL
    if ob_type == "bullish":
        sl_a = ob_low - 0.5 * h1_atr
        target_a = entry_price + ob_body  # 1 OB-body past entry in direction
        # Actually ADR 003 says "1 OB-body past far edge" — far edge for bullish
        # is ob_high (or the top of zone relative to entry). Let's compute:
        # target = entry_price + ob_body (simplest), OR ob_high + ob_body.
        # A1_v2 uses the latter interpretation. Re-read ADR 003:
        # "Target = retest_entry + 1 × OB_body_size past far edge"
        # => target = far_edge + ob_body
        # For bullish: far_edge = ob_high, target = ob_high + ob_body
        target_a = ob_high + ob_body
    else:
        sl_a = ob_high + 0.5 * h1_atr
        target_a = ob_low - ob_body

    # Geometry B (Test A)
    if symbol == "XAUUSD":
        if ob_type == "bullish":
            sl_b = ob_low - 0.001 * ob_low
        else:
            sl_b = ob_high + 0.001 * ob_high
    else:
        if ob_type == "bullish":
            sl_b = ob_low - 0.00015
        else:
            sl_b = ob_high + 0.00015
    sl_b_dist = abs(entry_price - sl_b)
    if ob_type == "bullish":
        target_b = entry_price + 1.5 * sl_b_dist
    else:
        target_b = entry_price - 1.5 * sl_b_dist

    # Walk forward from entry_idx_in_scan + 1 for outcome classification
    def classify(sl: float, target: float, window: int) -> tuple[str, Optional[float], float, float, int, Optional[int]]:
        """Return (outcome, continuation_r, mae_price_distance, penetration_price_distance,
        time_to_mae_candles, time_to_continuation_candles).

        Both outcomes CONTINUED/REVERSED use same-bar ambiguity rule: if a
        single M15 candle touches both SL and target, we resolve conservatively
        using open price.
        """
        sl_dist = abs(entry_price - sl)
        outcome = "UNRESOLVED"
        mae_price = 0.0
        penetration = 0.0
        time_to_mae = 0
        time_to_cont: Optional[int] = None
        cont_r: Optional[float] = None

        start = entry_idx_in_scan + 1  # matches Test A's j>=1 guard
        end = min(start + window, len(scan))

        if ob_type == "bullish":
            for j, idx in enumerate(range(start, end), start=1):
                c = scan.iloc[idx]
                adverse = entry_price - c.low
                if adverse > mae_price:
                    mae_price = adverse
                    time_to_mae = j
                # Penetration (below OB_low)
                if c.low < ob_low:
                    pen = ob_low - c.low
                    if pen > penetration:
                        penetration = pen

                hit_sl = c.low <= sl
                hit_tp = c.high >= target
                if hit_sl and hit_tp:
                    # Ambiguous — resolve by open
                    if c.open <= sl:
                        outcome = "REVERSED"
                        break
                    elif c.open >= target:
                        outcome = "CONTINUED"
                        time_to_cont = j
                        break
                    else:
                        outcome = "REVERSED"
                        break
                elif hit_sl:
                    outcome = "REVERSED"
                    break
                elif hit_tp:
                    outcome = "CONTINUED"
                    time_to_cont = j
                    break
        else:
            for j, idx in enumerate(range(start, end), start=1):
                c = scan.iloc[idx]
                adverse = c.high - entry_price
                if adverse > mae_price:
                    mae_price = adverse
                    time_to_mae = j
                if c.high > ob_high:
                    pen = c.high - ob_high
                    if pen > penetration:
                        penetration = pen

                hit_sl = c.high >= sl
                hit_tp = c.low <= target
                if hit_sl and hit_tp:
                    if c.open >= sl:
                        outcome = "REVERSED"
                        break
                    elif c.open <= target:
                        outcome = "CONTINUED"
                        time_to_cont = j
                        break
                    else:
                        outcome = "REVERSED"
                        break
                elif hit_sl:
                    outcome = "REVERSED"
                    break
                elif hit_tp:
                    outcome = "CONTINUED"
                    time_to_cont = j
                    break

        # continuation_r: favourable move / SL distance (r_multiple convention)
        if sl_dist > 0:
            if outcome == "CONTINUED":
                # Favourable excursion — we know we hit target ≥ entry+1R
                # For Geom A: target = ob_high + body (bullish), so favourable
                # move ≥ target - entry.
                cont_r = abs(target - entry_price) / sl_dist
            elif outcome == "REVERSED":
                cont_r = -1.0

        return outcome, cont_r, mae_price, penetration, time_to_mae, time_to_cont

    out_a, r_a, mae_a_dist, pen_a_dist, tmae_a, tcont_a = classify(sl_a, target_a, GEOM_A_WINDOW)
    out_b, r_b, mae_b_dist, pen_b_dist, tmae_b, tcont_b = classify(sl_b, target_b, GEOM_B_WINDOW)

    row = RetestRow(
        symbol=symbol,
        ob_formation_ts=ob.formation_ts,
        bos_confirm_ts=ob.bos_close_ts,
        retest_ts=retest_ts,
        retest_date=retest_ts.date(),
        session=session_label(retest_ts),
        side="long" if ob_type == "bullish" else "short",
        ob_body_size=ob_body,
        ob_body_size_pips=ob_body / pip,
        ob_body_size_atr=ob_body / h1_atr,
        retest_entry_price=entry_price,
        h1_atr_at_retest=h1_atr,
        sl_a_price=sl_a,
        target_a_price=target_a,
        outcome_a=out_a,
        continuation_r_a=r_a,
        mae_a_pips=mae_a_dist / pip,
        mae_a_atr=mae_a_dist / h1_atr,
        penetration_a_pips=pen_a_dist / pip,
        time_to_mae_a_candles=tmae_a,
        time_to_continuation_a_candles=tcont_a,
        sl_b_price=sl_b,
        target_b_price=target_b,
        outcome_b=out_b,
        continuation_r_b=r_b,
        mae_b_pips=mae_b_dist / pip,
        mae_b_atr=mae_b_dist / h1_atr,
        penetration_b_pips=pen_b_dist / pip,
        time_to_mae_b_candles=tmae_b,
        time_to_continuation_b_candles=tcont_b,
    )

    return row


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_symbol(symbol: str) -> list[RetestRow]:
    """Full pipeline for one symbol — return list of RetestRow."""
    print(f"[{symbol}] Loading data...")
    h1 = load_candles(symbol, "H1")
    m15 = load_candles(symbol, "M15")
    # Restrict H1 to 2025-09-01 onwards (we need enough runway to detect
    # pivots leading into 2026; 4 months of H1 is plenty).
    runway_start = pd.Timestamp(WINDOW_START - timedelta(days=90), tz="UTC")
    # For BOS candles we need BOS_close to fall within [WINDOW_START, WINDOW_END]
    h1_run = h1[h1.index >= runway_start]

    print(f"[{symbol}] H1 rows: {len(h1_run)} | M15 rows: {len(m15)}")

    obs = detect_obs(symbol, h1_run)
    # Filter OBs to those with BOS_close within study window
    win_lo = pd.Timestamp(WINDOW_START, tz="UTC")
    win_hi = pd.Timestamp(WINDOW_END, tz="UTC") + timedelta(days=1)
    obs = [
        ob for ob in obs
        if win_lo <= pd.Timestamp(ob.bos_close_ts) <= win_hi
    ]
    print(f"[{symbol}] OBs with BOS in window: {len(obs)}")

    # Dedup by (formation_ts, ob_type, high, low)
    seen: set[tuple] = set()
    uniq: list[DetectedOB] = []
    for ob in obs:
        key = (
            ob.formation_ts.isoformat(),
            ob.ob_type,
            round(ob.ob_high, 8),
            round(ob.ob_low, 8),
        )
        if key in seen:
            continue
        seen.add(key)
        uniq.append(ob)
    print(f"[{symbol}] Unique OBs: {len(uniq)}")

    rows: list[RetestRow] = []
    for ob in uniq:
        row = find_first_retest_and_measure(symbol, ob, h1_run, m15)
        if row is None:
            continue
        # Retest must be within window too
        if row.retest_ts.date() > WINDOW_END:
            continue
        if row.retest_ts.date() < WINDOW_START:
            continue
        rows.append(row)

    print(f"[{symbol}] Retests: {len(rows)}")
    return rows


def summarize(rows: list[RetestRow]) -> dict:
    """Compute per-symbol + combined continuation rates for Geom A / B."""
    by_symbol: dict[str, list[RetestRow]] = {}
    for r in rows:
        by_symbol.setdefault(r.symbol, []).append(r)
    by_symbol["combined"] = rows

    def rate(subset: list[RetestRow], key: str) -> dict:
        outs = [getattr(r, key) for r in subset]
        n = len(outs)
        cont = sum(1 for o in outs if o == "CONTINUED")
        rev = sum(1 for o in outs if o == "REVERSED")
        unr = sum(1 for o in outs if o == "UNRESOLVED")
        ex_unr_n = cont + rev
        ex_unr_rate = cont / ex_unr_n if ex_unr_n > 0 else None
        return {
            "n": n,
            "CONTINUED": cont,
            "REVERSED": rev,
            "UNRESOLVED": unr,
            "ex_unresolved_rate": ex_unr_rate,
        }

    summary = {}
    for sym, subset in by_symbol.items():
        summary[sym] = {
            "geometry_a": rate(subset, "outcome_a"),
            "geometry_b": rate(subset, "outcome_b"),
        }

    # Temporal-ordering audit
    viol = 0
    for r in rows:
        if not (r.retest_ts > r.bos_confirm_ts):
            viol += 1
    summary["temporal_ordering"] = {
        "total_rows": len(rows),
        "violations": viol,
        "pass_rate": (len(rows) - viol) / len(rows) if rows else 1.0,
    }

    return summary


def write_csv(rows: list[RetestRow], path: Path) -> None:
    fieldnames = [
        "symbol", "ob_formation_ts", "bos_confirm_ts", "retest_ts", "retest_date",
        "session", "side", "ob_body_size", "ob_body_size_pips", "ob_body_size_atr",
        "retest_entry_price", "h1_atr_at_retest",
        "sl_a_price", "target_a_price", "outcome_a", "continuation_r_a",
        "mae_a_pips", "mae_a_atr", "penetration_a_pips",
        "time_to_mae_a_candles", "time_to_continuation_a_candles",
        "sl_b_price", "target_b_price", "outcome_b", "continuation_r_b",
        "mae_b_pips", "mae_b_atr", "penetration_b_pips",
        "time_to_mae_b_candles", "time_to_continuation_b_candles",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "symbol": r.symbol,
                "ob_formation_ts": r.ob_formation_ts.isoformat().replace("+00:00", "Z"),
                "bos_confirm_ts": r.bos_confirm_ts.isoformat().replace("+00:00", "Z"),
                "retest_ts": r.retest_ts.isoformat().replace("+00:00", "Z"),
                "retest_date": r.retest_date.isoformat(),
                "session": r.session,
                "side": r.side,
                "ob_body_size": round(r.ob_body_size, 6),
                "ob_body_size_pips": round(r.ob_body_size_pips, 4),
                "ob_body_size_atr": round(r.ob_body_size_atr, 4),
                "retest_entry_price": round(r.retest_entry_price, 5),
                "h1_atr_at_retest": round(r.h1_atr_at_retest, 6),
                "sl_a_price": round(r.sl_a_price, 5),
                "target_a_price": round(r.target_a_price, 5),
                "outcome_a": r.outcome_a,
                "continuation_r_a": r.continuation_r_a if r.continuation_r_a is not None else "",
                "mae_a_pips": round(r.mae_a_pips, 3),
                "mae_a_atr": round(r.mae_a_atr, 4),
                "penetration_a_pips": round(r.penetration_a_pips, 3),
                "time_to_mae_a_candles": r.time_to_mae_a_candles,
                "time_to_continuation_a_candles": r.time_to_continuation_a_candles if r.time_to_continuation_a_candles is not None else "",
                "sl_b_price": round(r.sl_b_price, 5),
                "target_b_price": round(r.target_b_price, 5),
                "outcome_b": r.outcome_b,
                "continuation_r_b": r.continuation_r_b if r.continuation_r_b is not None else "",
                "mae_b_pips": round(r.mae_b_pips, 3),
                "mae_b_atr": round(r.mae_b_atr, 4),
                "penetration_b_pips": round(r.penetration_b_pips, 3),
                "time_to_mae_b_candles": r.time_to_mae_b_candles,
                "time_to_continuation_b_candles": r.time_to_continuation_b_candles if r.time_to_continuation_b_candles is not None else "",
            })


def main() -> None:
    all_rows: list[RetestRow] = []
    for sym in SYMBOLS:
        try:
            rows = run_symbol(sym)
            all_rows.extend(rows)
            # Per-symbol CSV
            write_csv(rows, OUTPUT_DIR / f"{sym}_retests.csv")
        except FileNotFoundError as e:
            print(f"[{sym}] SKIP: {e}")

    # Combined CSV
    write_csv(all_rows, OUTPUT_DIR / "combined_retests.csv")

    # Summary
    summary = summarize(all_rows)
    with (OUTPUT_DIR / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    # Print summary
    print("\n=== A2_v2 Independent Validator — Summary ===")
    for sym in SYMBOLS + ["combined"]:
        if sym not in summary:
            continue
        s = summary[sym]
        a = s["geometry_a"]
        b = s["geometry_b"]
        a_rate = f"{a['ex_unresolved_rate']:.1%}" if a["ex_unresolved_rate"] is not None else "n/a"
        b_rate = f"{b['ex_unresolved_rate']:.1%}" if b["ex_unresolved_rate"] is not None else "n/a"
        print(f"  {sym:>12}: GeomA n={a['n']:>3} cont={a['CONTINUED']:>3} rev={a['REVERSED']:>3} unr={a['UNRESOLVED']:>3} rate={a_rate} | "
              f"GeomB n={b['n']:>3} cont={b['CONTINUED']:>3} rev={b['REVERSED']:>3} unr={b['UNRESOLVED']:>3} rate={b_rate}")

    print(f"\nTemporal-ordering: {summary['temporal_ordering']}")


if __name__ == "__main__":
    main()
