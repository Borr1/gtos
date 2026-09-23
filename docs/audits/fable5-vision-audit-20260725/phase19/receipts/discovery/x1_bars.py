#!/usr/bin/env python3
"""x1_bars — shared bar loading for lane x1 (decision anatomy).

Loads the SAME M15 series the generator reads (lane-inputs true-UTC hold) and the M1
series inside each decision bar. Everything is positional, exactly as
src/components/broader_origin_generators.py indexes it.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta, timezone

HOLD = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M15_DIR = os.path.join(HOLD, "bridge_ftmo_m15_20250601_20260610")
M1_DIRS = [os.path.join(HOLD, f"bridge_ftmo_m1_{m}") for m in ("202512", "202601", "202602")]

SYMBOLS = ['AUDJPY', 'AUDUSD', 'BTCUSD', 'CHFJPY', 'ETHUSD', 'EURGBP', 'EURJPY', 'EURUSD',
           'GBPJPY', 'GBPUSD', 'GER40', 'JP225', 'NAS100', 'NZDUSD', 'SPX500', 'UK100',
           'UKOIL_cash', 'US30_cash', 'USDCAD', 'USDCHF', 'USDJPY', 'USOIL_cash',
           'XAGUSD', 'XAUUSD']


def _pt(s: str) -> datetime:
    return datetime.fromisoformat(s).astimezone(timezone.utc).replace(tzinfo=None)


def load_csv(path):
    """-> list of (time_naive_utc, o, h, l, c, v) sorted by time."""
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.append((_pt(row["time"]), float(row["open"]), float(row["high"]),
                        float(row["low"]), float(row["close"]),
                        float(row.get("volume") or 0.0)))
    out.sort(key=lambda r: r[0])
    return out


def load_m15(symbols=SYMBOLS):
    """-> {symbol: (bars_list, {time: positional_index})}"""
    out = {}
    for s in symbols:
        p = os.path.join(M15_DIR, f"{s}_M15.csv")
        if not os.path.isfile(p):
            continue
        bars = load_csv(p)
        out[s] = (bars, {b[0]: i for i, b in enumerate(bars)})
    return out


def load_m1(symbols=SYMBOLS, months=("202512", "202601", "202602")):
    """-> {symbol: {minute_time: (o,h,l,c,v)}}"""
    out = {}
    for s in symbols:
        d = {}
        for m in months:
            p = os.path.join(HOLD, f"bridge_ftmo_m1_{m}", f"{s}_M1.csv")
            if not os.path.isfile(p):
                continue
            for t, o, h, lo, c, v in load_csv(p):
                d[t] = (o, h, lo, c, v)
        out[s] = d
    return out


# ---- generator-identical feature helpers (broader_origin_generators.py:2265-2306) ----
def prior_high(bars, index, lookback):
    start = max(0, index - lookback)
    return max(b[2] for b in bars[start:index]) if index > start else None


def prior_low(bars, index, lookback):
    start = max(0, index - lookback)
    return min(b[3] for b in bars[start:index]) if index > start else None


def atr(bars, index, lookback):
    if index < 0:
        return None
    start = max(0, index - lookback + 1)
    win = bars[start:index + 1]
    return (sum(b[2] - b[3] for b in win) / len(win)) if win else None


def close_position(bars, index, lookback):
    start = max(0, index - lookback + 1)
    win = bars[start:index + 1]
    hi = max(b[2] for b in win)
    lo = min(b[3] for b in win)
    if hi <= lo:
        return None
    return (bars[index][4] - lo) / (hi - lo)


def trend_state(bars, index, atr50):
    if index < 20 or atr50 is None or atr50 <= 0:
        return "insufficient_lookback"
    score = (bars[index][4] - bars[index - 20][4]) / atr50
    if score >= 2.0:
        return "strong_up"
    if score >= 0.75:
        return "up"
    if score <= -2.0:
        return "strong_down"
    if score <= -0.75:
        return "down"
    return "flat"


def previous_trend_state(bars, index):
    if index <= 0:
        return "insufficient_lookback"
    return trend_state(bars, index - 1, atr(bars, index - 1, 50))


def m1_slice(m1_by_sym, symbol, bar_open, n=15):
    """The n M1 bars inside an M15 bar opening at bar_open. Missing minutes are skipped;
    returns [(minute_index_0_based, t, o,h,l,c,v)] for the minutes that exist."""
    d = m1_by_sym.get(symbol) or {}
    out = []
    for k in range(n):
        t = bar_open + timedelta(minutes=k)
        row = d.get(t)
        if row is not None:
            out.append((k, t, *row))
    return out
