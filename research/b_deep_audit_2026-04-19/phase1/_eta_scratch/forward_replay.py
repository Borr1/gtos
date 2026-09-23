"""Forward-replay helpers.

Determine, given a signal candle_time, what would have won at +1.5R in either direction
within a forward horizon — where R is measured as a multiple of M15 ATR-14 computed AT SIGNAL CLOSE
(no look-ahead).

Core logic:
  We consider both a hypothetical LONG and a hypothetical SHORT from the signal candle close.
  SL = 1× ATR_m15 on each side. TP = 1.5× ATR_m15 on the opposite side.
  Winner = first direction where TP is hit before SL on the forward path.
  UNKNOWN = neither side resolves within horizon.
  CONFLICT = both sides "win" within the same later candle (ambiguous — coin flip).

This gives us a fair, symmetric "price would have hit +1.5R in direction X" label.

CALIBRATION: 1.5R matches min_rr in production. SL = 1× ATR is a standard baseline.
Using larger SL (1.5× ATR, 2× ATR) is offered as a sensitivity knob.
"""
from __future__ import annotations

from typing import Optional

from load_data import atr_14, find_candle_idx, find_candle_idx_at_or_before


def replay_hypothetical(candles_m15, signal_idx, horizon_minutes=4 * 60,
                        sl_atr_mult=1.0, tp_atr_mult=1.5):
    """From the close of candles_m15[signal_idx], replay both LONG and SHORT hypotheticals.

    Uses the OPEN of the following candle as the fill (or close of signal candle if no next).

    Returns dict:
      entry_price, atr, bars_horizon,
      long_outcome  ∈ {'WIN', 'LOSS', 'OPEN'},
      short_outcome ∈ {'WIN', 'LOSS', 'OPEN'},
      winner ∈ {'LONG', 'SHORT', 'NONE', 'CONFLICT'},
      bars_to_resolve_winner (int or None).
    """
    n = len(candles_m15)
    if signal_idx is None or signal_idx >= n - 1:
        return None
    atr = atr_14(candles_m15, signal_idx)
    if atr is None or atr <= 0:
        return None

    entry = candles_m15[signal_idx]["close"]
    long_sl = entry - sl_atr_mult * atr
    long_tp = entry + tp_atr_mult * atr
    short_sl = entry + sl_atr_mult * atr
    short_tp = entry - tp_atr_mult * atr

    bars_horizon = max(1, horizon_minutes // 15)

    long_outcome = "OPEN"
    short_outcome = "OPEN"
    long_res_bar = None
    short_res_bar = None

    for k in range(1, bars_horizon + 1):
        j = signal_idx + k
        if j >= n:
            break
        h = candles_m15[j]["high"]
        l = candles_m15[j]["low"]

        # LONG path
        if long_outcome == "OPEN":
            hit_tp = h >= long_tp
            hit_sl = l <= long_sl
            if hit_tp and hit_sl:
                long_outcome = "LOSS"  # Pessimistic — assume SL hit first within the bar
                long_res_bar = k
            elif hit_tp:
                long_outcome = "WIN"
                long_res_bar = k
            elif hit_sl:
                long_outcome = "LOSS"
                long_res_bar = k

        # SHORT path
        if short_outcome == "OPEN":
            hit_tp = l <= short_tp
            hit_sl = h >= short_sl
            if hit_tp and hit_sl:
                short_outcome = "LOSS"
                short_res_bar = k
            elif hit_tp:
                short_outcome = "WIN"
                short_res_bar = k
            elif hit_sl:
                short_outcome = "LOSS"
                short_res_bar = k

        if long_outcome != "OPEN" and short_outcome != "OPEN":
            break

    if long_outcome == "WIN" and short_outcome != "WIN":
        winner = "LONG"
        res_bar = long_res_bar
    elif short_outcome == "WIN" and long_outcome != "WIN":
        winner = "SHORT"
        res_bar = short_res_bar
    elif long_outcome == "WIN" and short_outcome == "WIN":
        winner = "CONFLICT"
        res_bar = min(long_res_bar or 9999, short_res_bar or 9999)
    else:
        winner = "NONE"
        res_bar = None

    return {
        "entry": entry,
        "atr": atr,
        "bars_horizon": bars_horizon,
        "long_outcome": long_outcome,
        "short_outcome": short_outcome,
        "winner": winner,
        "bars_to_resolve_winner": res_bar,
        "sl_atr_mult": sl_atr_mult,
        "tp_atr_mult": tp_atr_mult,
    }
