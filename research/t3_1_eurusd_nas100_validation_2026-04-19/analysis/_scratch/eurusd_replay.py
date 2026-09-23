"""EURUSD M15 CSV replay engine — mirror of scripts/simulate_t7_live_period.py::compute_outcome().

Loads EURUSD_M15.csv once, indexed by candle_time (ISO string, UTC naive). Given a
candidate-like dict (candle_time/entry/sl/tp/direction/candle_close), replays the
forward candles and returns outcome.

Key fidelity note:
- Production sim uses _FILL_EPSILON = 0.05 POINTS. On EURUSD that is 0.05 price
  units = 500 pips — effectively ALL limits are "at-market". We keep that default
  for bit-exact reproduction of sim behaviour, but expose a parameter so callers
  can override with a tighter 0.0001 (1 pip) check for sensitivity.
- SL checked before TP within the same candle (conservative → LOSS wins the tie).
"""

from __future__ import annotations
import csv
import os
from dataclasses import dataclass, field
from typing import Iterable

from eurusd_extract import M15_CSV


@dataclass
class M15Candle:
    time: str       # naive UTC "YYYY-MM-DD HH:MM:SS" string
    open: float
    high: float
    low: float
    close: float


@dataclass
class ReplayResult:
    outcome: str              # WIN / LOSS / UNFILLED / OPEN / UNKNOWN
    r_multiple: float | None = None
    exit_candle: str | None = None
    fill_candle: str | None = None
    reason: str = ""
    mae_pre_fill: float | None = None   # max adverse excursion before fill (price units)
    mfe_pre_fill: float | None = None
    mae_post_fill: float | None = None  # after fill, in R
    mfe_post_fill: float | None = None


_CANDLES: list[M15Candle] | None = None
_TIME_INDEX: dict[str, int] | None = None


def _load_csv() -> list[M15Candle]:
    global _CANDLES, _TIME_INDEX
    if _CANDLES is not None:
        return _CANDLES
    out: list[M15Candle] = []
    with open(M15_CSV, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out.append(M15Candle(
                time=row["time"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            ))
    _CANDLES = out
    _TIME_INDEX = {c.time: i for i, c in enumerate(out)}
    return out


def _normalize_time(ct: str) -> str:
    """Convert sim candle_time '2026-01-07T09:30:00Z' to CSV format '2026-01-07 09:30:00'."""
    return ct.replace("T", " ").replace("Z", "")


def replay(
    candidate: dict,
    *,
    fill_epsilon: float = 0.05,
    max_bars: int | None = None,
    post_fill_timeout_bars: int | None = None,
) -> ReplayResult:
    """Replay a single candidate's trade on EURUSD M15 CSV.

    Args:
        candidate: dict with keys candle_time, entry_price, stop_loss,
            take_profit_1, direction, candle_close.
        fill_epsilon: sim-faithful default 0.05. Use 0.0001 (1 pip) for stricter
            sensitivity test.
        max_bars: cap on how many bars to search after candle_time. None = no cap.
        post_fill_timeout_bars: if provided, treat fill+this bars as BE exit
            (for the 2h-timeout variant: 8 bars).
    """
    _load_csv()
    assert _CANDLES is not None and _TIME_INDEX is not None
    entry = candidate.get("entry_price")
    sl = candidate.get("stop_loss")
    tp = candidate.get("take_profit_1")
    direction = candidate.get("direction", "LONG")
    candle_close = candidate.get("candle_close")
    candle_time = candidate["candle_time"]

    if not entry or not sl or not tp:
        return ReplayResult(outcome="UNKNOWN", reason="missing_prices")

    # Guard against zero-risk degenerate inputs (EURUSD 2-dp rounding)
    if direction == "LONG":
        if sl >= entry or tp <= entry:
            return ReplayResult(outcome="UNKNOWN", reason="degenerate_zero_risk")
    else:
        if sl <= entry or tp >= entry:
            return ReplayResult(outcome="UNKNOWN", reason="degenerate_zero_risk")

    norm_time = _normalize_time(candle_time)
    start_idx = _TIME_INDEX.get(norm_time)
    if start_idx is None:
        return ReplayResult(outcome="UNKNOWN", reason=f"candle_time_not_in_csv:{norm_time}")

    needs_fill_check = (candle_close is not None) and (abs(entry - candle_close) > fill_epsilon)
    entry_filled = not needs_fill_check
    fill_candle_time: str | None = None if not entry_filled else norm_time
    fill_idx: int | None = None if not entry_filled else start_idx

    mae_pre = 0.0
    mfe_pre = 0.0
    mae_r = 0.0
    mfe_r = 0.0
    sl_dist = abs(entry - sl)

    for i in range(start_idx + 1, len(_CANDLES)):
        if max_bars is not None and (i - start_idx) > max_bars:
            break
        c = _CANDLES[i]

        if not entry_filled:
            # Track pre-fill excursions relative to entry
            if direction == "LONG":
                adverse = entry - c.low   # positive = price went below entry
                favour = c.high - entry
            else:
                adverse = c.high - entry
                favour = entry - c.low
            if adverse > mae_pre:
                mae_pre = adverse
            if favour > mfe_pre:
                mfe_pre = favour

            if direction == "LONG":
                if entry < candle_close and c.low <= entry:
                    entry_filled = True
                elif entry > candle_close and c.high >= entry:
                    entry_filled = True
            else:
                if entry > candle_close and c.high >= entry:
                    entry_filled = True
                elif entry < candle_close and c.low <= entry:
                    entry_filled = True
            if entry_filled:
                fill_candle_time = c.time
                fill_idx = i
            else:
                continue

        # Post-fill: track MAE/MFE in R
        if sl_dist > 0:
            if direction == "LONG":
                adv = (entry - c.low) / sl_dist
                fav = (c.high - entry) / sl_dist
            else:
                adv = (c.high - entry) / sl_dist
                fav = (entry - c.low) / sl_dist
            if adv > mae_r:
                mae_r = adv
            if fav > mfe_r:
                mfe_r = fav

        # Optional timeout-BE exit
        if post_fill_timeout_bars is not None and fill_idx is not None:
            if (i - fill_idx) >= post_fill_timeout_bars:
                return ReplayResult(
                    outcome="BE", r_multiple=0.0, exit_candle=c.time,
                    fill_candle=fill_candle_time,
                    mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre,
                    mae_post_fill=mae_r, mfe_post_fill=mfe_r,
                )

        # Normal SL-first, TP-second:
        if direction == "LONG":
            if c.low <= sl:
                return ReplayResult(
                    outcome="LOSS", r_multiple=-1.0, exit_candle=c.time,
                    fill_candle=fill_candle_time,
                    mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre,
                    mae_post_fill=mae_r, mfe_post_fill=mfe_r,
                )
            if c.high >= tp:
                r = (tp - entry) / sl_dist
                return ReplayResult(
                    outcome="WIN", r_multiple=round(r, 2), exit_candle=c.time,
                    fill_candle=fill_candle_time,
                    mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre,
                    mae_post_fill=mae_r, mfe_post_fill=mfe_r,
                )
        else:
            if c.high >= sl:
                return ReplayResult(
                    outcome="LOSS", r_multiple=-1.0, exit_candle=c.time,
                    fill_candle=fill_candle_time,
                    mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre,
                    mae_post_fill=mae_r, mfe_post_fill=mfe_r,
                )
            if c.low <= tp:
                r = (entry - tp) / sl_dist
                return ReplayResult(
                    outcome="WIN", r_multiple=round(r, 2), exit_candle=c.time,
                    fill_candle=fill_candle_time,
                    mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre,
                    mae_post_fill=mae_r, mfe_post_fill=mfe_r,
                )

    if not entry_filled:
        return ReplayResult(outcome="UNFILLED", reason="entry_limit_never_reached",
                             mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre)
    return ReplayResult(outcome="OPEN", reason="no_exit_in_data",
                         mae_pre_fill=mae_pre, mfe_pre_fill=mfe_pre,
                         mae_post_fill=mae_r, mfe_post_fill=mfe_r,
                         fill_candle=fill_candle_time)


def forward_excursion(candle_time: str, bars: int = 8) -> dict:
    """Compute max favourable / adverse / net excursion over the next N candles
    (pure CSV, no entry). Returns dict with up_exc / down_exc / net / start_close
    in price units.
    """
    _load_csv()
    assert _CANDLES is not None and _TIME_INDEX is not None
    norm = _normalize_time(candle_time)
    i = _TIME_INDEX.get(norm)
    if i is None:
        return {"error": f"candle_time_not_in_csv:{norm}"}
    start_close = _CANDLES[i].close
    hi = max(c.high for c in _CANDLES[i+1 : i+1+bars]) if i+1 < len(_CANDLES) else start_close
    lo = min(c.low for c in _CANDLES[i+1 : i+1+bars]) if i+1 < len(_CANDLES) else start_close
    last_close = _CANDLES[min(i+bars, len(_CANDLES)-1)].close
    return {
        "start_close": start_close,
        "fwd_high": hi,
        "fwd_low": lo,
        "up_exc": hi - start_close,      # price units
        "down_exc": start_close - lo,
        "net": last_close - start_close,
    }


if __name__ == "__main__":
    _load_csv()
    print(f"Loaded {len(_CANDLES)} M15 candles; first={_CANDLES[0].time} last={_CANDLES[-1].time}")
