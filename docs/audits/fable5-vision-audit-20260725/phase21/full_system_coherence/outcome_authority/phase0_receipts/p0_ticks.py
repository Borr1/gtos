#!/usr/bin/env python3
"""Phase 0 T1 — inverted-entry cost from the broker tick archive.

The tick archive covers broker wall 2026-06-18..07-26, i.e. true UTC
2026-06-17T21:00 .. 2026-07-25T21:00 (the offset is a constant +3 h across the whole
window: US EDT, `new_york_plus_7`). That covers part of the June read window and most
of July. Nothing outside it is claimed as measured.

For every MARKET candidate whose decision instant falls inside tick coverage this
measures, at the exact trigger instants:

  quoted spread   ask - bid at the last tick at or before the decision instant, and
                  at the modelled fill instant (the successor M1 bar open).
  latency drift   direction x (executable-entry-side quote at t_d + lambda
                  - at t_d), for lambda in {0.1, 0.25, 1, 5} s. This is the genuine
                  execution slippage of a market order sent at the decision.
  model timing    direction x (executable-entry-side quote at the modelled fill
                  instant - at t_d): what the labeler's 60-second-late fill costs
                  relative to a fill at the decision.

All three are reported for the ORIGINAL direction; the inverted direction is the
exact negation of the drift terms and carries the same spread.
"""
from __future__ import annotations

import bz2
import datetime as dt
import gzip
import json
import os
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

TICKS = Path("/Users/borr/GTOSActive/vps-ticks-20260726/ftmo")
OUT = Path("/private/tmp/phase0-inversion")
OFFSET_MS = 3 * 3600 * 1000  # broker wall -> UTC, constant over the archive window

# 24-symbol surface -> tick-archive file symbol
SYMBOL_FILE = {
    "GER40": "GER40_cash",
    "JP225": "JP225_cash",
    "NAS100": "US100_cash",
    "SPX500": "US500_cash",
    "UK100": "UK100_cash",
}
LAMBDAS_MS = (100, 250, 1000, 5000)

T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def load_queries():
    """(symbol -> list of query dicts) from the walk output, tick-covered rows only."""
    lo = int(dt.datetime(2026, 6, 17, 21, 0, tzinfo=dt.timezone.utc).timestamp() * 1000)
    hi = int(dt.datetime(2026, 7, 25, 20, 0, tzinfo=dt.timezone.utc).timestamp() * 1000)
    by_symbol = defaultdict(list)
    for month in ("jun", "jul"):
        path = OUT / f"walk_{month}.pkl.gz"
        if not path.is_file():
            continue
        for rec in pickle.load(gzip.open(path, "rb")):
            fill = rec["orig"].get("fill_time")
            if not fill:
                continue
            t_d = int(
                dt.datetime.fromisoformat(rec["decision_utc"].replace("Z", "+00:00")).timestamp()
                * 1000
            )
            t_f = int(
                dt.datetime.fromisoformat(fill.replace("Z", "+00:00")).timestamp() * 1000
            )
            if not (lo <= t_d <= hi and lo <= t_f <= hi):
                continue
            by_symbol[rec["symbol"]].append(
                {
                    "key": rec["key"],
                    "month": month,
                    "family": rec["family"],
                    "side": rec["side"],
                    "t_d": t_d,
                    "t_f": t_f,
                    "risk": rec["risk_price"],
                    "risk_inv": rec["risk_price_inv"],
                    "model_spread_r": rec["spread_r"],
                }
            )
    return by_symbol


def read_ticks(symbol: str):
    """(utc_ms, bid, ask) arrays for one symbol, streamed from the gz export."""
    name = SYMBOL_FILE.get(symbol, symbol)
    matches = sorted(TICKS.glob(f"FTMO_{name}_ticks_*.csv.gz"))
    if not matches:
        return None
    times, bids, asks = [], [], []
    with gzip.open(matches[0], "rt", newline="") as handle:
        header = handle.readline().rstrip("\n").split(",")
        i_bid, i_ask, i_msc = header.index("bid"), header.index("ask"), header.index("time_msc")
        for line in handle:
            parts = line.rstrip("\n").split(",")
            try:
                bid = float(parts[i_bid])
                ask = float(parts[i_ask])
            except (ValueError, IndexError):
                continue
            if bid <= 0 or ask <= 0 or ask < bid:
                continue
            times.append(int(parts[i_msc]) - OFFSET_MS)
            bids.append(bid)
            asks.append(ask)
    if not times:
        return None
    t = np.asarray(times, dtype=np.int64)
    order = np.argsort(t, kind="stable")
    return t[order], np.asarray(bids)[order], np.asarray(asks)[order]


def measure(symbol, queries, arrays):
    t, bid, ask = arrays
    out = []
    # index of the last tick at or before each instant
    def at(instants):
        idx = np.searchsorted(t, instants, side="right") - 1
        return idx

    t_d = np.asarray([q["t_d"] for q in queries], dtype=np.int64)
    t_f = np.asarray([q["t_f"] for q in queries], dtype=np.int64)
    i_d, i_f = at(t_d), at(t_f)
    lam = {ms: at(t_d + ms) for ms in LAMBDAS_MS}
    for n, q in enumerate(queries):
        a, b = i_d[n], i_f[n]
        if a < 0 or b < 0:
            continue
        # staleness guard: the quote must be recent enough to describe the instant
        stale_d = int(t_d[n] - t[a])
        stale_f = int(t_f[n] - t[b])
        direction = 1 if q["side"] == "LONG" else -1
        entry_at = lambda i: (ask[i] if direction > 0 else bid[i])
        row = {
            "key": q["key"],
            "symbol": symbol,
            "month": q["month"],
            "family": q["family"],
            "side": q["side"],
            "risk": q["risk"],
            "risk_inv": q["risk_inv"],
            "model_spread_r": q["model_spread_r"],
            "true_spread_decision": float(ask[a] - bid[a]),
            "true_spread_fill": float(ask[b] - bid[b]),
            "stale_ms_decision": stale_d,
            "stale_ms_fill": stale_f,
            # the labeler's 60 s-late fill, priced against a decision-instant fill,
            # signed against the ORIGINAL direction, in ORIGINAL risk units
            "model_timing_r": float(direction * (entry_at(b) - entry_at(a)) / q["risk"])
            if q["risk"] > 0
            else None,
        }
        for ms in LAMBDAS_MS:
            j = lam[ms][n]
            row[f"latency_r_{ms}"] = (
                float(direction * (entry_at(j) - entry_at(a)) / q["risk"])
                if j >= 0 and q["risk"] > 0
                else None
            )
            row[f"latency_stale_ms_{ms}"] = int(t_d[n] + ms - t[j]) if j >= 0 else None
        out.append(row)
    return out


def main():
    by_symbol = load_queries()
    log(stage="queries", symbols=len(by_symbol), n=sum(len(v) for v in by_symbol.values()))
    results = []
    for symbol in sorted(by_symbol):
        arrays = read_ticks(symbol)
        if arrays is None:
            log(stage="no_ticks", symbol=symbol)
            continue
        rows = measure(symbol, by_symbol[symbol], arrays)
        results.extend(rows)
        log(stage="symbol", symbol=symbol, ticks=int(arrays[0].size), measured=len(rows))
        del arrays
    with gzip.open(OUT / "tick_costs.pkl.gz", "wb") as fh:
        pickle.dump(results, fh, protocol=5)
    log(stage="done", n=len(results))


if __name__ == "__main__":
    main()
