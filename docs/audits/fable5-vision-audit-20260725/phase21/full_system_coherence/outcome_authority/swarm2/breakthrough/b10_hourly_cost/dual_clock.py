"""B10 addendum -- the surface in BOTH clocks, and the DST smear priced.

Why this file exists
--------------------
The rollover is a BROKER-clock event: it happens at broker 00:00 every day, forever.  The
estate buckets by UTC hour.  Those two agree only while the broker offset is constant, and
it is not: broker wall = ``America/New_York + 7`` (`src/utils/broker_clock.py`), so the
offset is **+3 h under EDT and +2 h under EST**.  Broker 00:00 is therefore

    UTC 21:00  from the second Sunday in March to the first Sunday in November
    UTC 22:00  the rest of the year

**A UTC hour bucket spanning a DST boundary contains the rollover for part of its rows and
not for the rest.**  The spike is split across two buckets, which simultaneously
*understates* the expensive hour and *contaminates* a cheap one.  B10's own tape window
(2026-06-18..07-26) is entirely inside EDT, so B10's surface is NOT smeared -- but any
estate artifact bucketed by UTC hour over a span longer than one DST regime is.

This module

  1. republishes every hour cell keyed by BROKER wall hour as well as UTC hour, with the
     rollover cell named explicitly in both clocks;
  2. prices the smear: what a naive year-long UTC-hour bucket would report for the
     rollover hour and for its cheap neighbour, against the true broker-hour values;
  3. measures the CLOSE-anchored spread specifically -- the last quarter-hour before
     broker midnight -- because a close-anchored daily signal samples exactly that minute
     and not the hour's average.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import sys

import numpy as np

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

NY = ZoneInfo("America/New_York") if ZoneInfo else None
BROKER_OFFSET_FROM_NY_H = 7      # src/utils/broker_clock.py rule `new_york_plus_7`
SURFACE_24 = ("AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
              "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
              "SPX500", "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
              "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD")
CANON_TO_FILE = {"NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
                 "JP225": "JP225_cash", "UK100": "UK100_cash", "US30_cash": "US30_cash"}


def broker_offset_hours(day: dt.date) -> int:
    """+3 under EDT, +2 under EST -- measured, not assumed."""
    if NY is None:
        return 3
    noon_ny = dt.datetime(day.year, day.month, day.day, 12, tzinfo=NY)
    ny_off = noon_ny.utcoffset().total_seconds() / 3600.0     # -4 EDT, -5 EST
    return int(round(ny_off + BROKER_OFFSET_FROM_NY_H))


def dst_regime_days(year: int) -> dict[int, int]:
    """offset -> number of days in that regime, for one calendar year."""
    out: dict[int, int] = {}
    d = dt.date(year, 1, 1)
    while d.year == year:
        out[broker_offset_hours(d)] = out.get(broker_offset_hours(d), 0) + 1
        d += dt.timedelta(days=1)
    return out


def main(tape_json: str, subhour_json: str, out_json: str) -> None:
    tape = json.load(open(tape_json))
    sub = json.load(open(subhour_json))
    window_off = 3   # verified constant across 2026-06-18..07-26

    regimes = {y: dst_regime_days(y) for y in (2025, 2026)}
    r26 = regimes[2026]
    tot26 = sum(r26.values())
    share_edt = r26.get(3, 0) / tot26
    share_est = r26.get(2, 0) / tot26

    dual = {}
    smear = {}
    close_anchor = {}
    for canon in SURFACE_24:
        f = CANON_TO_FILE.get(canon, canon)
        blk = (tape["accounts"].get("FTMO") or {}).get(f)
        if not blk:
            continue
        by_utc = blk["by_hour_utc"]
        rows = {}
        for h in range(24):
            c = by_utc.get(str(h))
            if not c:
                rows[h] = {"utc_hour": h, "broker_hour": (h + window_off) % 24,
                           "coverage": "MARKET_CLOSED"}
                continue
            rows[h] = {
                "utc_hour": h, "broker_hour": (h + window_off) % 24,
                "is_broker_rollover_in_this_window": (h + window_off) % 24 == 0,
                "n_ticks": c["n_ticks"], "median_px": c["q_tick"]["p50"],
                "mean_px": c["mean_px"], "mean_bps": c["mean_bps"],
                "median_mult": c["median_mult"],
            }
        dual[canon] = {"broker_wall_to_utc_offset_in_window_h": window_off, "hours": rows}

        # --- the smear: a naive year-long UTC bucket blends two broker hours ---
        # under EDT: UTC h  == broker h+3 ;  under EST: UTC h == broker h+2
        def cell(uh):
            c = by_utc.get(str(uh % 24))
            return c["mean_px"] if c else None

        # broker 00 sits at UTC 21 (EDT) and UTC 22 (EST)
        b00_edt, b23_edt, b01_edt = cell(21), cell(20), cell(22)
        if b00_edt is None:
            smear[canon] = {"coverage": "MARKET_CLOSED_AT_BROKER_ROLLOVER"}
            continue
        # In-window we can only observe the EDT mapping, so the EST-regime value for a
        # given BROKER hour is taken from the same broker hour -- the rollover premium is
        # a broker-clock property, which is the whole point.
        naive_utc21 = share_edt * b00_edt + share_est * (b23_edt if b23_edt else b00_edt)
        naive_utc22 = share_edt * (b01_edt if b01_edt else b00_edt) + share_est * b00_edt
        smear[canon] = {
            "true_broker_h00_mean_px": b00_edt,
            "true_broker_h23_mean_px": b23_edt,
            "true_broker_h01_mean_px": b01_edt,
            "naive_utc21_bucket_annual": naive_utc21,
            "naive_utc22_bucket_annual": naive_utc22,
            "utc21_understates_rollover_by_pct": 100 * (1 - naive_utc21 / b00_edt),
            "utc22_overstates_cheap_hour_by_x": (naive_utc22 / b01_edt) if b01_edt else None,
            "edt_share_of_year": share_edt, "est_share_of_year": share_est,
        }

        # --- close-anchored: the last quarter-hour before broker midnight ---
        sblk = (sub["accounts"].get("FTMO") or {}).get(f)
        if sblk:
            q = sblk["by_hour_quarter_utc"]
            last = q.get("20|3")          # UTC 20:45-21:00 = broker 23:45-00:00
            typ = [v["mean_px"] for k, v in q.items()
                   if 7 <= int(k.split("|")[0]) <= 15]
            if last and typ:
                ref = blk["reference"]["median_px"]
                close_anchor[canon] = {
                    "close_quarter_utc": "20:45-21:00", "close_quarter_broker": "23:45-00:00",
                    "n_ticks": last["n_ticks"],
                    "close_mean_px": last["mean_px"],
                    "typical_session_mean_px": float(np.median(typ)),
                    "ratio": last["mean_px"] / float(np.median(typ)),
                    "close_mult_vs_reference_p50": last["mean_px"] / ref if ref else None,
                }

    doc = {
        "schema": "b10_dual_clock_and_dst_v1",
        "clock": {
            "rule": "broker wall = America/New_York + 7 (src/utils/broker_clock.py)",
            "offset_h_under_EDT": 3, "offset_h_under_EST": 2,
            "broker_rollover_lands_at_UTC": {"EDT": 21, "EST": 22},
            "b10_tape_window": "2026-06-18..07-26, entirely EDT -- B10's own surface is "
                               "NOT smeared; it is a single-regime measurement",
            "dst_regime_days_2026": r26,
            "edt_share_of_year": share_edt, "est_share_of_year": share_est,
            "2026_transitions": ["2026-03-08 (EST->EDT)", "2026-11-01 (EDT->EST)"],
            "why_it_matters": "a UTC hour bucket spanning a DST boundary contains the "
                              "broker rollover for part of its rows and not the rest, so it "
                              "understates the expensive hour AND contaminates a cheap one",
        },
        "dual_clock_surface": dual,
        "dst_smear": smear,
        "close_anchored_spread": close_anchor,
    }
    json.dump(doc, open(out_json, "w"), indent=1)

    print(f"DST 2026: EDT {r26.get(3)} d ({share_edt:.1%}), EST {r26.get(2)} d ({share_est:.1%})")
    print("broker 00:00 = UTC 21:00 under EDT, UTC 22:00 under EST\n")
    print(f"{'symbol':11s} {'b23':>9s} {'b00':>9s} {'b01':>9s} | "
          f"{'naiveUTC21':>10s} {'under%':>7s} | {'naiveUTC22':>10s} {'over x':>7s}")
    for s, v in smear.items():
        if v.get("coverage"):
            print(f"{s:11s} {v['coverage']}")
            continue
        print(f"{s:11s} {(v['true_broker_h23_mean_px'] or 0):9.5f} "
              f"{v['true_broker_h00_mean_px']:9.5f} "
              f"{(v['true_broker_h01_mean_px'] or 0):9.5f} | "
              f"{v['naive_utc21_bucket_annual']:10.5f} "
              f"{v['utc21_understates_rollover_by_pct']:6.1f}% | "
              f"{v['naive_utc22_bucket_annual']:10.5f} "
              f"{(v['utc22_overstates_cheap_hour_by_x'] or 0):6.2f}x")
    print(f"\n{'symbol':11s} {'close px':>10s} {'session px':>11s} {'ratio':>7s} "
          f"{'vs ref p50':>10s}  n")
    for s, v in sorted(close_anchor.items(), key=lambda kv: -kv[1]["ratio"]):
        print(f"{s:11s} {v['close_mean_px']:10.5f} {v['typical_session_mean_px']:11.5f} "
              f"{v['ratio']:7.2f} {v['close_mult_vs_reference_p50']:10.2f}  {v['n_ticks']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
