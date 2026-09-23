"""A2 Independent Validation — Retest Geometry Study.

Rebuilds the core numbers of A1's Retest Geometry Study with an INDEPENDENT
code path — pandas-only, no imports from src/components/, no shared helpers
with research/retest_geometry/study.py or scripts/ob_retest_comprehensive.py.

Purpose
-------
Cross-check A1's headline 92.9% continuation rate and distributional findings
(touch-only vs pierce, MAE tercile, MAE percentiles) using a simpler but
defensible OB detector and a re-implemented walk-forward classifier.

Methodology
-----------
OB detection (H1):
    A "bullish OB" is the last bearish H1 candle (close < open) before a
    confirmed bullish break-of-structure (BOS).

    BOS (bullish) is confirmed when an H1 candle CLOSES above the most recent
    swing high. Swing high = a 3-bar local max (H[i-1] > H[i-2], H[i-1] > H[i]).
    Mirror definitions for bearish OBs.

    Freshness: OB is valid only if the zone has NOT been touched between
    formation and the current M15 candle being scanned for retest.
    (A zone is "touched" if any intervening M15 low/high enters ob_low..ob_high.)

Retest (M15):
    First M15 candle after OB formation whose low (bullish) or high (bearish)
    enters [ob_low, ob_high]. We use the same "enter body" definition A1 uses.
    Entry price: candle close if close is inside OB body, else next candle
    open. (Matches A1.)

Classifier:
    - 1R target: entry + ob_body_size past far edge (same as A1).
    - SL: opposing edge + 0.5 * H1 ATR(14). (Same as A1.)
    - Walk forward 48 M15 candles (12h) starting from retest candle.
    - CONTINUED = 1R hit. REVERSED = SL hit. UNRESOLVED = neither.
    - If SL + TP hit same candle, conservatively call REVERSED unless the
      candle open is already beyond TP.

Inputs:
    data/historical/{SYMBOL}_H1.csv
    data/historical/{SYMBOL}_M15.csv

Outputs:
    research/retest_geometry/outputs/a2_validation/{SYMBOL}_retests.csv
    research/retest_geometry/outputs/a2_validation/combined_retests.csv
    research/retest_geometry/outputs/a2_validation/summary.json

Run:
    python research/retest_geometry/A2_validation.py
"""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
log = logging.getLogger("A2_validation")


# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "historical"
OUT_DIR = (
    PROJECT_ROOT
    / "research"
    / "retest_geometry"
    / "outputs"
    / "a2_validation"
)

SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]
STUDY_START = date(2026, 1, 1)
STUDY_END = date(2026, 4, 17)

RESOLUTION_HORIZON = 48  # M15 candles
SL_MARGIN_ATR = 0.5       # H1 ATR units
ATR_PERIOD = 14
SCAN_WINDOW_M15 = 192     # retest scan window from OB formation (48h)

# Pip sizes (match A1)
PIP_SIZE = {
    "XAUUSD": 0.1,
    "US30_cash": 1.0,
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "GBPUSD": 0.0001,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_candles(symbol: str, tf: str) -> pd.DataFrame:
    """Load OHLCV CSV into a DataFrame with a UTC DatetimeIndex."""
    path = DATA_DIR / f"{symbol}_{tf}.csv"
    df = pd.read_csv(path)
    # The CSVs are naive UTC strings like "2024-04-01 01:00:00"
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# ATR (Wilder) — pandas implementation, independent of production
# ---------------------------------------------------------------------------


def compute_atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR on an OHLC DataFrame. Returns a Series aligned to df.index.

    The ATR at row i uses the 14 preceding True Range values (standard Wilder).
    """
    h = df["high"]
    l = df["low"]
    c = df["close"]
    prev_c = c.shift(1)
    tr = pd.concat(
        [
            (h - l),
            (h - prev_c).abs(),
            (l - prev_c).abs(),
        ],
        axis=1,
    ).max(axis=1)
    # Wilder = EMA with alpha = 1/period (after a seed of the simple mean).
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return atr


# ---------------------------------------------------------------------------
# OB detection — independent of production
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OrderBlock:
    symbol: str
    side: str                   # "bullish" | "bearish"
    formation_time: pd.Timestamp
    formation_idx: int          # index into H1 df
    bos_idx: int                # index of the H1 candle that confirmed BOS
    ob_high: float
    ob_low: float
    ob_open: float
    ob_close: float


def _swing_highs(df: pd.DataFrame) -> np.ndarray:
    """Boolean array: True at index i if df.iloc[i-1] is a 3-bar swing high.

    Uses a STRICT 3-bar definition on highs:
        H[i-2] < H[i-1]   AND   H[i-1] > H[i]
    We mark the swing AT index i-1. For convenience we return an array of
    the same length as df and set True at the swing index.
    """
    n = len(df)
    mask = np.zeros(n, dtype=bool)
    h = df["high"].to_numpy()
    for i in range(1, n - 1):
        if h[i] > h[i - 1] and h[i] > h[i + 1]:
            mask[i] = True
    return mask


def _swing_lows(df: pd.DataFrame) -> np.ndarray:
    n = len(df)
    mask = np.zeros(n, dtype=bool)
    l = df["low"].to_numpy()
    for i in range(1, n - 1):
        if l[i] < l[i - 1] and l[i] < l[i + 1]:
            mask[i] = True
    return mask


def detect_order_blocks(
    h1: pd.DataFrame,
    symbol: str,
    start_date: date,
    end_date: date,
) -> list[OrderBlock]:
    """Detect fresh H1 order blocks.

    Algorithm (simplest defensible definition):
    1. Identify 3-bar swing highs / lows across the full H1 series.
    2. For each bullish BOS (close above most recent confirmed swing high),
       walk backward from the BOS candle to find the last bearish candle
       (close < open). That candle is the bullish OB.
    3. Symmetric for bearish BOS.
    4. Filter OBs whose BOS candle falls in [start_date, end_date].

    Only one BOS per swing-high (first touch only) — avoids retriggering on
    noisy continuation candles.
    """
    n = len(h1)
    highs = h1["high"].to_numpy()
    lows = h1["low"].to_numpy()
    closes = h1["close"].to_numpy()
    opens = h1["open"].to_numpy()
    times = h1["time"].to_numpy()

    swing_hi_mask = _swing_highs(h1)
    swing_lo_mask = _swing_lows(h1)

    obs: list[OrderBlock] = []

    # --- Bullish OBs: walk forward; track the most recent swing high; when
    #     a candle closes above it, fire a BOS and find the prior bearish
    #     candle.
    last_swing_hi_idx: Optional[int] = None
    fired_swing_hi: set[int] = set()
    for i in range(2, n):
        # Update most recent confirmed swing high (confirmation requires the
        # 3-bar to be complete, so available at i >= swing_idx + 1).
        if i >= 2 and swing_hi_mask[i - 1]:
            last_swing_hi_idx = i - 1
        if last_swing_hi_idx is None:
            continue
        if last_swing_hi_idx in fired_swing_hi:
            continue
        if closes[i] > highs[last_swing_hi_idx]:
            # BOS fired. Walk backward from i-1 to last_swing_hi_idx to find
            # the most recent bearish candle (close < open).
            ob_idx: Optional[int] = None
            for k in range(i - 1, last_swing_hi_idx - 1, -1):
                if closes[k] < opens[k]:
                    ob_idx = k
                    break
            fired_swing_hi.add(last_swing_hi_idx)
            if ob_idx is None:
                continue
            # The OB zone is the candle's high-low range (use full range,
            # same convention as A1 which uses ob.high/ob.low).
            obs.append(
                OrderBlock(
                    symbol=symbol,
                    side="bullish",
                    formation_time=pd.Timestamp(times[ob_idx]),
                    formation_idx=ob_idx,
                    bos_idx=i,
                    ob_high=float(highs[ob_idx]),
                    ob_low=float(lows[ob_idx]),
                    ob_open=float(opens[ob_idx]),
                    ob_close=float(closes[ob_idx]),
                )
            )

    # --- Bearish OBs
    last_swing_lo_idx: Optional[int] = None
    fired_swing_lo: set[int] = set()
    for i in range(2, n):
        if i >= 2 and swing_lo_mask[i - 1]:
            last_swing_lo_idx = i - 1
        if last_swing_lo_idx is None:
            continue
        if last_swing_lo_idx in fired_swing_lo:
            continue
        if closes[i] < lows[last_swing_lo_idx]:
            ob_idx: Optional[int] = None
            for k in range(i - 1, last_swing_lo_idx - 1, -1):
                if closes[k] > opens[k]:
                    ob_idx = k
                    break
            fired_swing_lo.add(last_swing_lo_idx)
            if ob_idx is None:
                continue
            obs.append(
                OrderBlock(
                    symbol=symbol,
                    side="bearish",
                    formation_time=pd.Timestamp(times[ob_idx]),
                    formation_idx=ob_idx,
                    bos_idx=i,
                    ob_high=float(highs[ob_idx]),
                    ob_low=float(lows[ob_idx]),
                    ob_open=float(opens[ob_idx]),
                    ob_close=float(closes[ob_idx]),
                )
            )

    # Filter by BOS date (the study window is about when we would have
    # observed the OB as "fresh" — i.e., after the BOS confirms it).
    filtered = []
    start_ts = pd.Timestamp(start_date, tz="UTC")
    end_ts = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    for ob in obs:
        bos_time = pd.Timestamp(h1["time"].iloc[ob.bos_idx])
        if bos_time >= start_ts and bos_time < end_ts:
            filtered.append(ob)
    return filtered


# ---------------------------------------------------------------------------
# Retest detection — independent of production
# ---------------------------------------------------------------------------


@dataclass
class RetestRecord:
    symbol: str
    ob_formation_ts: str
    retest_ts: str
    retest_date: str
    session: str
    side: str
    ob_body_size_pips: float
    ob_body_size_atr: float
    ob_body_size_pct_price: float
    retest_entry_price: float
    mae_pips: float
    mae_atr: float
    mae_pct_ob_body: float
    penetration_pips: float
    penetration_atr: float
    time_to_mae_candles: int
    time_to_continuation_candles: Optional[int]
    outcome: str
    continuation_r: Optional[float]
    # Extras (not in A1's schema but needed for cross-check)
    touched_only: bool
    pierced: bool
    h1_atr: float
    entry_idx: int


def _session_label(ts: pd.Timestamp) -> str:
    """Match A1's collapsed session semantics (reference: study.py)."""
    h = ts.hour
    # London: 07:00 - 13:00 UTC (london_open/body)
    if 7 <= h < 13:
        return "London"
    # NY: 13:00 - 20:00 UTC (overlap/open/afternoon)
    if 13 <= h < 20:
        return "NY"
    # Tokyo / asian: 00:00 - 07:00
    if 0 <= h < 7:
        return "Tokyo"
    return "None"


def _find_h1_atr_at(h1: pd.DataFrame, atr: pd.Series, target_ts: pd.Timestamp) -> float:
    """Return the most recent H1 ATR value at or strictly before target_ts."""
    mask = h1["time"] < target_ts
    if not mask.any():
        return 0.0
    pos = mask[mask].index[-1]
    val = atr.iloc[pos]
    if pd.isna(val):
        return 0.0
    return float(val)


def classify_retest(
    ob: OrderBlock,
    m15: pd.DataFrame,
    h1: pd.DataFrame,
    atr_h1: pd.Series,
    symbol: str,
) -> Optional[RetestRecord]:
    """Detect first retest on M15 after OB formation and classify outcome.

    Returns None if no retest found within scan window.
    """
    pip = PIP_SIZE.get(symbol, 0.0001)
    # Locate start index in m15 (first m15 candle strictly AFTER ob formation)
    ob_ts = ob.formation_time
    # H1 candle at hour H is the period [H:00, H+1:00). OB formation_time in
    # the CSV is the start of the hour. M15 candles strictly after ob_ts means
    # m15.time > ob_ts, i.e. the M15 candle at the H1 candle close hour's next
    # 15-min bucket. Same convention as A1.
    start_mask = m15["time"] > ob_ts
    if not start_mask.any():
        return None
    start_idx = start_mask[start_mask].index[0]
    end_idx = min(start_idx + SCAN_WINDOW_M15, len(m15))

    m15_times = m15["time"].to_numpy()
    m15_o = m15["open"].to_numpy()
    m15_h = m15["high"].to_numpy()
    m15_l = m15["low"].to_numpy()
    m15_c = m15["close"].to_numpy()

    # Freshness: ensure no M15 candle BETWEEN formation_time and the first
    # retest has already entered the OB body. Since we return on the FIRST
    # entering candle, the "freshness" requirement is automatically met —
    # any earlier candle that entered would be the first retest.

    retest_idx = None
    for i in range(start_idx, end_idx):
        low = m15_l[i]
        high = m15_h[i]
        if ob.side == "bullish":
            # Enters zone: any part of candle touches [ob_low, ob_high]
            if low <= ob.ob_high and high >= ob.ob_low:
                retest_idx = i
                break
        else:
            if high >= ob.ob_low and low <= ob.ob_high:
                retest_idx = i
                break
    if retest_idx is None:
        return None

    # Entry price selection (match A1)
    retest_close = m15_c[retest_idx]
    if ob.side == "bullish":
        if retest_close >= ob.ob_low:
            entry_price = float(retest_close)
            entry_idx = retest_idx
        elif retest_idx + 1 < len(m15):
            entry_price = float(m15_o[retest_idx + 1])
            entry_idx = retest_idx + 1
        else:
            return None
    else:
        if retest_close <= ob.ob_high:
            entry_price = float(retest_close)
            entry_idx = retest_idx
        elif retest_idx + 1 < len(m15):
            entry_price = float(m15_o[retest_idx + 1])
            entry_idx = retest_idx + 1
        else:
            return None

    # H1 ATR at retest
    retest_ts = pd.Timestamp(m15_times[retest_idx])
    h1_atr = _find_h1_atr_at(h1, atr_h1, retest_ts)
    if h1_atr <= 0:
        return None

    # SL
    ob_body = max(ob.ob_high - ob.ob_low, 1e-9)
    if ob.side == "bullish":
        sl_price = ob.ob_low - SL_MARGIN_ATR * h1_atr
        target_price = entry_price + ob_body
    else:
        sl_price = ob.ob_high + SL_MARGIN_ATR * h1_atr
        target_price = entry_price - ob_body

    # Walk forward
    outcome = "UNRESOLVED"
    time_to_continuation: Optional[int] = None
    continuation_r: Optional[float] = None
    mae_value = 0.0
    time_to_mae = 0
    penetration_value = 0.0

    horizon_end = min(entry_idx + RESOLUTION_HORIZON + 1, len(m15))
    forward = range(entry_idx, horizon_end)

    # Track whether the retest ever pierced the OB edge vs touch-only.
    # Definition: pierced = price at any point during the retest candle OR the
    # walk-forward window pierced PAST the OB edge into the SL direction.
    # For "touch-only" we look only at the retest candle's MAE vs OB edge.
    pierced_during_entry_scan = False

    for j_offset, j in enumerate(forward):
        low = float(m15_l[j])
        high = float(m15_h[j])
        open_ = float(m15_o[j])

        if ob.side == "bullish":
            adverse = entry_price - low
            if adverse > mae_value:
                mae_value = adverse
                time_to_mae = j_offset
            if low < ob.ob_low:
                pen = ob.ob_low - low
                if pen > penetration_value:
                    penetration_value = pen
                pierced_during_entry_scan = True

            if j_offset >= 1:
                sl_hit = low <= sl_price
                tp_hit = high >= target_price
                if sl_hit and tp_hit:
                    if open_ <= sl_price:
                        outcome = "REVERSED"
                        break
                    if open_ >= target_price:
                        outcome = "CONTINUED"
                        time_to_continuation = j_offset
                        continuation_r = (high - entry_price) / ob_body
                        break
                    outcome = "REVERSED"
                    break
                if sl_hit:
                    outcome = "REVERSED"
                    break
                if tp_hit:
                    outcome = "CONTINUED"
                    time_to_continuation = j_offset
                    continuation_r = (high - entry_price) / ob_body
                    break
        else:
            adverse = high - entry_price
            if adverse > mae_value:
                mae_value = adverse
                time_to_mae = j_offset
            if high > ob.ob_high:
                pen = high - ob.ob_high
                if pen > penetration_value:
                    penetration_value = pen
                pierced_during_entry_scan = True

            if j_offset >= 1:
                sl_hit = high >= sl_price
                tp_hit = low <= target_price
                if sl_hit and tp_hit:
                    if open_ >= sl_price:
                        outcome = "REVERSED"
                        break
                    if open_ <= target_price:
                        outcome = "CONTINUED"
                        time_to_continuation = j_offset
                        continuation_r = (entry_price - low) / ob_body
                        break
                    outcome = "REVERSED"
                    break
                if sl_hit:
                    outcome = "REVERSED"
                    break
                if tp_hit:
                    outcome = "CONTINUED"
                    time_to_continuation = j_offset
                    continuation_r = (entry_price - low) / ob_body
                    break

    pierced = penetration_value > 0
    touched_only = not pierced

    record = RetestRecord(
        symbol=symbol,
        ob_formation_ts=pd.Timestamp(ob.formation_time).strftime("%Y-%m-%dT%H:%M:%SZ"),
        retest_ts=pd.Timestamp(retest_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
        retest_date=pd.Timestamp(retest_ts).strftime("%Y-%m-%d"),
        session=_session_label(pd.Timestamp(retest_ts)),
        side="long" if ob.side == "bullish" else "short",
        ob_body_size_pips=round(ob_body / pip, 4),
        ob_body_size_atr=round(ob_body / h1_atr, 4),
        ob_body_size_pct_price=round(ob_body / entry_price * 100, 6) if entry_price else 0.0,
        retest_entry_price=round(entry_price, 5),
        mae_pips=round(mae_value / pip, 4),
        mae_atr=round(mae_value / h1_atr, 4),
        mae_pct_ob_body=round(mae_value / ob_body * 100, 4) if ob_body else 0.0,
        penetration_pips=round(penetration_value / pip, 4),
        penetration_atr=round(penetration_value / h1_atr, 4),
        time_to_mae_candles=int(time_to_mae),
        time_to_continuation_candles=time_to_continuation,
        outcome=outcome,
        continuation_r=round(continuation_r, 4) if continuation_r is not None else None,
        touched_only=touched_only,
        pierced=pierced,
        h1_atr=round(h1_atr, 6),
        entry_idx=entry_idx,
    )
    return record


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_symbol(symbol: str) -> tuple[list[RetestRecord], int, int]:
    """Run the pipeline for one symbol. Returns (records, n_obs, n_retested)."""
    log.info(f"=== {symbol} ===")
    h1 = load_candles(symbol, "H1")
    m15 = load_candles(symbol, "M15")
    log.info(f"  H1 candles: {len(h1)}   M15 candles: {len(m15)}")

    atr_h1 = compute_atr_series(h1, ATR_PERIOD)

    obs = detect_order_blocks(h1, symbol, STUDY_START, STUDY_END)
    log.info(f"  fresh OBs detected (BOS in window): {len(obs)}")

    records: list[RetestRecord] = []
    for ob in obs:
        r = classify_retest(ob, m15, h1, atr_h1, symbol)
        if r is not None:
            records.append(r)
    log.info(
        f"  retests found: {len(records)}   "
        f"(CONTINUED={sum(1 for r in records if r.outcome=='CONTINUED')} "
        f"REVERSED={sum(1 for r in records if r.outcome=='REVERSED')} "
        f"UNRESOLVED={sum(1 for r in records if r.outcome=='UNRESOLVED')})"
    )
    return records, len(obs), len(records)


def summarize(records: list[RetestRecord]) -> dict:
    if not records:
        return {"n": 0}
    df = pd.DataFrame([asdict(r) for r in records])
    out = {}
    for sym, group in df.groupby("symbol"):
        n = len(group)
        cont = (group["outcome"] == "CONTINUED").sum()
        rev = (group["outcome"] == "REVERSED").sum()
        unr = (group["outcome"] == "UNRESOLVED").sum()
        out[sym] = {
            "n": int(n),
            "continued": int(cont),
            "reversed": int(rev),
            "unresolved": int(unr),
            "pct_continued": round(cont / n * 100, 2),
            "pct_reversed": round(rev / n * 100, 2),
            "pct_unresolved": round(unr / n * 100, 2),
            "ex_unresolved_continuation_rate": round(
                cont / max(cont + rev, 1) * 100, 2
            ),
        }
    total_n = len(df)
    total_cont = (df["outcome"] == "CONTINUED").sum()
    total_rev = (df["outcome"] == "REVERSED").sum()
    total_unr = (df["outcome"] == "UNRESOLVED").sum()
    out["_combined"] = {
        "n": int(total_n),
        "continued": int(total_cont),
        "reversed": int(total_rev),
        "unresolved": int(total_unr),
        "pct_continued": round(total_cont / total_n * 100, 2),
        "pct_reversed": round(total_rev / total_n * 100, 2),
        "pct_unresolved": round(total_unr / total_n * 100, 2),
        "ex_unresolved_continuation_rate": round(
            total_cont / max(total_cont + total_rev, 1) * 100, 2
        ),
    }
    return out


def distributional_findings(records: list[RetestRecord]) -> dict:
    """Reproduce A1's key distributional checks.

    1. MAE percentiles (ATR units) for XAUUSD and USDJPY.
    2. Touch-only vs pierce continuation split.
    3. MAE tercile continuation.
    """
    df = pd.DataFrame([asdict(r) for r in records])
    out: dict = {}

    # 1. MAE percentiles by symbol
    mae_percentiles = {}
    for sym, group in df.groupby("symbol"):
        p = group["mae_atr"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).round(3).tolist()
        mae_percentiles[sym] = {
            "n": len(group),
            "p10": p[0],
            "p25": p[1],
            "p50": p[2],
            "p75": p[3],
            "p90": p[4],
        }
    out["mae_percentiles_atr"] = mae_percentiles

    # 2. Touch-only vs pierce
    resolved = df[df["outcome"].isin(["CONTINUED", "REVERSED"])]
    touch = resolved[~resolved["pierced"]]
    pier = resolved[resolved["pierced"]]
    out["touch_only"] = {
        "n": len(touch),
        "continued": int((touch["outcome"] == "CONTINUED").sum()),
        "pct_continued": round(
            (touch["outcome"] == "CONTINUED").sum() / max(len(touch), 1) * 100, 2
        ),
    }
    out["pierced"] = {
        "n": len(pier),
        "continued": int((pier["outcome"] == "CONTINUED").sum()),
        "pct_continued": round(
            (pier["outcome"] == "CONTINUED").sum() / max(len(pier), 1) * 100, 2
        ),
    }

    # 3. MAE tercile (on resolved retests)
    if len(resolved) >= 3:
        terciles = resolved["mae_atr"].quantile([1 / 3, 2 / 3]).tolist()
        t1, t2 = terciles[0], terciles[1]

        def bucket(val):
            if val <= t1:
                return "low"
            if val <= t2:
                return "mid"
            return "high"

        resolved = resolved.assign(tercile=resolved["mae_atr"].apply(bucket))
        tercile_stats = {}
        for label in ("low", "mid", "high"):
            sub = resolved[resolved["tercile"] == label]
            n = len(sub)
            c = int((sub["outcome"] == "CONTINUED").sum())
            tercile_stats[label] = {
                "n": n,
                "continued": c,
                "pct_continued": round(c / max(n, 1) * 100, 2),
            }
        out["mae_tercile_cutpoints"] = {"low_high": round(t1, 3), "mid_high": round(t2, 3)}
        out["mae_tercile_stats"] = tercile_stats

    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--symbols",
        default=",".join(SYMBOLS),
        help="Comma-separated list of symbols",
    )
    args = parser.parse_args(argv)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_records: list[RetestRecord] = []
    per_symbol_ob_counts: dict[str, int] = {}
    for sym in symbols:
        recs, n_obs, _ = run_symbol(sym)
        per_symbol_ob_counts[sym] = n_obs
        all_records.extend(recs)
        if recs:
            df = pd.DataFrame([asdict(r) for r in recs])
            df.to_csv(OUT_DIR / f"{sym}_retests.csv", index=False)

    if all_records:
        df = pd.DataFrame([asdict(r) for r in all_records])
        df.to_csv(OUT_DIR / "combined_retests.csv", index=False)

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "study_window": {"start": str(STUDY_START), "end": str(STUDY_END)},
        "symbols": symbols,
        "fresh_ob_counts": per_symbol_ob_counts,
        "outcome_summary": summarize(all_records),
        "distributional_findings": distributional_findings(all_records),
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    log.info("Wrote summary.json")
    log.info(
        f"TOTAL: n={len(all_records)}  "
        f"CONTINUED={sum(1 for r in all_records if r.outcome=='CONTINUED')}  "
        f"REVERSED={sum(1 for r in all_records if r.outcome=='REVERSED')}  "
        f"UNRESOLVED={sum(1 for r in all_records if r.outcome=='UNRESOLVED')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
