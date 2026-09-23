"""B10 stage 1 -- reduce one broker tick file to an hourly spread tape.

Emits, per file, a compressed npz holding:

  cell grid   168 cells = weekday_utc * 24 + hour_utc  (UTC, converted from broker wall
              clock by the measured +3 h offset for this export window; see
              `src/utils/broker_clock.py` rule ``new_york_plus_7``, NY=EDT throughout
              2026-06-18..07-26 so the offset is constant and verified in the report)

  per cell    n_ticks, dwell_s, sp_sum (tick-wt), sp_dwell (time-wt), sp_sq,
              sp_min, sp_max, mid_sum, mid_dwell

  histograms  hist_tick[168, 400] and hist_dwell[168, 400] over log10(spread_price),
              40 bins/decade from 1e-6 to 1e4.  Log-linear interpolation inside a bin
              gives quantiles far finer than the 5.9 % bin width.  Quantiles are the
              point: the spike is a TAIL phenomenon and a mean hides it.

  m15 bars    per M15 bucket: n, sp_min, sp_sum, dwell, sp_dwell.  This is the
              instrument for the "bar spread column is the within-bar MINIMUM" defect --
              min vs mean, measured, per bar, from the tape the bar was cut from.

  day x hour  n and sp_sum per (utc_date, utc_hour) so downstream can day-cluster
              bootstrap rather than assume i.i.d. ticks.

Dwell time is the gap to the next tick, capped at DWELL_CAP_S so one weekend hole cannot
dominate an hour.  Tick-weighted and time-weighted are both kept because they answer
different questions: a market order pays the spread at ONE instant (time-weighted is the
unbiased estimate of that instant's cost), while tick-weighted over-weights fast markets.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

NB = 400            # 40 bins per decade
LOG_LO = -6.0
BINS_PER_DECADE = 40
DWELL_CAP_S = 60.0  # a gap longer than this is a market hole, not dwell at that spread
BROKER_TO_UTC_S = 3 * 3600   # measured; constant across this export window
M15 = 900


def reduce_file(path: str, out: str) -> dict:
    base = os.path.basename(path)
    broker = "FTMO" if base.startswith("FTMO") else "redacted_account"
    sym = base.split("_ticks_")[0].replace("FTMO_", "").replace("redacted_account_", "")

    cell_n = np.zeros(168)
    cell_dwell = np.zeros(168)
    cell_sp = np.zeros(168)
    cell_spd = np.zeros(168)
    cell_sq = np.zeros(168)
    cell_min = np.full(168, np.inf)
    cell_max = np.zeros(168)
    cell_mid = np.zeros(168)
    cell_midd = np.zeros(168)
    hist_t = np.zeros((168, NB))
    hist_d = np.zeros((168, NB))

    m15: dict[int, list[float]] = {}      # bucket -> [n, sp_min, sp_sum, dwell, sp_dwell]
    dh: dict[tuple[int, int], list[float]] = {}   # (utc_day, hour) -> [n, sp_sum, dwell, sp_dwell]

    n_tot = 0
    n_bad = 0
    n_inv = 0
    carry_t = None   # last tick's utc second, for dwell across chunk boundary
    carry_sp = None
    carry_mid = None

    reader = pd.read_csv(
        path,
        usecols=["time", "time_msc", "bid", "ask"],
        dtype={"time": "int64", "time_msc": "int64", "bid": "float64", "ask": "float64"},
        chunksize=4_000_000,
    )
    for ch in reader:
        n_tot += len(ch)
        b = ch["bid"].to_numpy()
        a = ch["ask"].to_numpy()
        tms = ch["time_msc"].to_numpy()
        ok = np.isfinite(b) & np.isfinite(a) & (b > 0) & (a > 0)
        n_bad += int((~ok).sum())
        b, a, tms = b[ok], a[ok], tms[ok]
        inv = a < b
        n_inv += int(inv.sum())
        keep = ~inv
        b, a, tms = b[keep], a[keep], tms[keep]
        if len(b) == 0:
            continue

        # broker ms -> utc seconds (float, keeps sub-second dwell)
        tu = tms / 1000.0 - BROKER_TO_UTC_S
        order = np.argsort(tu, kind="stable")
        tu, b, a = tu[order], b[order], a[order]
        sp = a - b
        mid = (a + b) * 0.5

        # dwell = gap to next tick; the carried last tick of the previous chunk supplies
        # the first gap, so no tick is silently dropped from the time-weighted mass.
        if carry_t is not None:
            tu = np.concatenate(([carry_t], tu))
            sp = np.concatenate(([carry_sp], sp))
            mid = np.concatenate(([carry_mid], mid))
        gap = np.diff(tu, append=tu[-1])
        dwell = np.clip(gap, 0.0, DWELL_CAP_S)
        carry_t, carry_sp, carry_mid = tu[-1], sp[-1], mid[-1]
        # drop the final tick from this chunk's accumulation; it is carried forward
        tu, sp, mid, dwell = tu[:-1], sp[:-1], mid[:-1], dwell[:-1]
        if len(tu) == 0:
            continue

        ts = tu.astype("int64")
        day = ts // 86400
        hour = (ts % 86400) // 3600
        weekday = (day + 4) % 7          # 1970-01-01 was a Thursday
        cell = (weekday * 24 + hour).astype("int64")

        np.add.at(cell_n, cell, 1.0)
        np.add.at(cell_dwell, cell, dwell)
        np.add.at(cell_sp, cell, sp)
        np.add.at(cell_spd, cell, sp * dwell)
        np.add.at(cell_sq, cell, sp * sp)
        np.add.at(cell_mid, cell, mid)
        np.add.at(cell_midd, cell, mid * dwell)
        np.minimum.at(cell_min, cell, sp)
        np.maximum.at(cell_max, cell, sp)

        with np.errstate(divide="ignore"):
            lg = np.log10(np.maximum(sp, 1e-12))
        bi = np.clip(((lg - LOG_LO) * BINS_PER_DECADE).astype("int64"), 0, NB - 1)
        flat = cell * NB + bi
        np.add.at(hist_t.reshape(-1), flat, 1.0)
        np.add.at(hist_d.reshape(-1), flat, dwell)

        bkt = ts // M15
        ub, idx = np.unique(bkt, return_index=True)
        end = np.append(idx[1:], len(bkt))
        cnt = (end - idx).astype("float64")
        smin = np.minimum.reduceat(sp, idx)
        ssum = np.add.reduceat(sp, idx)
        dsum = np.add.reduceat(dwell, idx)
        sdsum = np.add.reduceat(sp * dwell, idx)
        for i, k in enumerate(ub):
            r = m15.get(int(k))
            v = (cnt[i], smin[i], ssum[i], dsum[i], sdsum[i])
            if r is None:
                m15[int(k)] = list(v)
            else:
                r[0] += v[0]
                r[1] = min(r[1], v[1])
                r[2] += v[2]
                r[3] += v[3]
                r[4] += v[4]

        dkey = day * 100 + hour
        ud, idx2 = np.unique(dkey, return_index=True)
        end2 = np.append(idx2[1:], len(dkey))
        c2 = (end2 - idx2).astype("float64")
        s2 = np.add.reduceat(sp, idx2)
        d2 = np.add.reduceat(dwell, idx2)
        sd2 = np.add.reduceat(sp * dwell, idx2)
        for i, k in enumerate(ud):
            key = (int(k) // 100, int(k) % 100)
            r = dh.get(key)
            v = (c2[i], s2[i], d2[i], sd2[i])
            if r is None:
                dh[key] = list(v)
            else:
                for j in range(4):
                    r[j] += v[j]

    cell_min[~np.isfinite(cell_min)] = 0.0
    mk = np.array(sorted(m15.keys()), dtype="int64")
    mv = np.array([m15[k] for k in mk], dtype="float64") if len(mk) else np.zeros((0, 5))
    dk = np.array(sorted(dh.keys()), dtype="int64") if dh else np.zeros((0, 2), dtype="int64")
    dv = np.array([dh[tuple(k)] for k in dk], dtype="float64") if len(dk) else np.zeros((0, 4))

    np.savez_compressed(
        out,
        cell_n=cell_n, cell_dwell=cell_dwell, cell_sp=cell_sp, cell_spd=cell_spd,
        cell_sq=cell_sq, cell_min=cell_min, cell_max=cell_max, cell_mid=cell_mid,
        cell_midd=cell_midd, hist_tick=hist_t, hist_dwell=hist_d,
        m15_bucket=mk, m15_stats=mv, dayhour_key=dk, dayhour_stats=dv,
        symbol=sym, broker=broker, n_ticks=n_tot, n_bad=n_bad, n_inverted=n_inv,
        nb=NB, log_lo=LOG_LO, bins_per_decade=BINS_PER_DECADE,
        dwell_cap_s=DWELL_CAP_S, broker_to_utc_s=BROKER_TO_UTC_S,
    )
    return {"file": base, "symbol": sym, "broker": broker, "ticks": int(n_tot),
            "bad": int(n_bad), "inverted": int(n_inv), "cells": int((cell_n > 0).sum()),
            "m15_bars": int(len(mk))}


if __name__ == "__main__":
    print(json.dumps(reduce_file(sys.argv[1], sys.argv[2])), flush=True)
